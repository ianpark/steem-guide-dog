"""
Bot
"""

import asyncio
import os
import json
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from feed import Feed
from performer import Performer
from datetime import datetime
from db import DataStore
from collections import deque


CONFIG_FILE_PATH = 'etc/config.json'

class Bot:
    executor = ThreadPoolExecutor(max_workers=4)
    def __init__(self):
        with open(CONFIG_FILE_PATH) as config:    
            self.config = json.load(config)
        self.loop = asyncio.get_event_loop()
        self.feed = Feed(self.config, self.on_data)
        self.queue = deque()
        self.posters = deque()
        self.db = DataStore(self.config)
        keypath = os.path.expanduser(self.config['keyfile_path'])
        with open(keypath) as keyfile:    
            keyfile_json = json.load(keyfile)
            for poster in self.config['posters']:
                self.posters.append(
                    Performer(self.config,
                            poster,
                            keyfile_json[poster['account']],
                            self.on_complete))
        self.run_flag = True
    
    def on_data(self, post):
        """ Should not block this function """
        print ('Append data: %s' % post )
        self.queue.append(post)
    
    def on_complete(self, result):
        print ('Finished: %s' % result)
        self.loop.call_later(20, self.posters.append, result['poster'])
        if not result['result']:
            print ('Append data to the left: %s' % result['post'] )
            self.queue.appendleft(result['post'])

    def is_valid(self, post):
        if post['author'] == post['parent_author']:
            print ('Author and parent author is the same')
            return False
        if post['author'] in self.config['blacklist']:
            print ('Black list match: ignore the report from %s' % post['author'])
            return False
        if post['parent_author'] in self.config['whitelist']:
            print ('White list match: ignore the report for %s' % post['parent_author'])
            return False
        return True

    def save_report(self, post):
        result = self.db.store_report(
            {
                'reporter': post['author'],
                'author': post['parent_author'],
                'permlink': post['parent_permlink'],
                'report_time': datetime.now(),
                'bot_signal': post['bot_signal']
            })
        return result

    def leave_comment(self, post):
        post['reported_count'] = self.db.get_reported_count(post['parent_author'])
        self.posters.popleft().leave_comment(post)

    async def work(self):
        print ('Start Bot')
        loop = asyncio.get_event_loop()
        while self.run_flag:
            # Poll the queue every second
            await asyncio.sleep(1)
            while len(self.queue):
                if self.posters:
                    post = self.queue.popleft()
                    try:
                        print ('%s reported %s' % (post['author'], post['parent_author']))
                        if not self.is_valid(post):
                            print ('not valid')
                            break
                        if not self.save_report(post):
                            print ('failed to save')
                            break
                        # Dispatch the past to the idle poster
                        self.leave_comment(post)
                    except Exception as e:
                        print ('Error! %s' % e)
                        pass
                else:
                    print ("No idle poster. Queue length=%s" % len(self.queue))
                    break
        self.feed.stop()

    def run(self):
        self.feed.start()
        return self.loop.run_until_complete(self.work())

    def stop(self):
        print ('Stopping Bot')
        self.run_flag = False
        self.feed.stop()