"""
Bot
"""

import asyncio
import json
import logging
import os

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from feed import Feed
from performer import Performer
from datetime import datetime
from db import DataStore
from collections import deque
from webapp import run_webapp


CONFIG_FILE_PATH = 'etc/config.json'

class Bot:
    executor = ThreadPoolExecutor(max_workers=4)
    log = logging.getLogger(__name__)
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
        self.executor.submit(run_webapp, self.config, self.db)
    
    def on_data(self, post):
        """ Should not block this function """
        self.log.info('Append data: %s' % post )
        self.queue.append(post)
    
    def on_complete(self, result):
        self.log.info('Finished: %s' % result)
        self.loop.call_later(20, self.posters.append, result['poster'])
        if not result['result']:
            self.log.info('Append data to the left: %s' % result['post'] )
            self.queue.appendleft(result['post'])

    def is_valid(self, post):
        if post['signal_type'] == 'praise':
            # Block self praise
            if post['author'] == post['parent_author']:
                self.log.info('Author and parent author is the same')
                return False
        elif post['signal_type'] == 'spam':
            if post['author'] == post['parent_author']:
                self.log.info('Author and parent author is the same')
                return False
            if post['author'] in self.config['blacklist']:
                self.log.info('Black list match: ignore the report from %s' % post['author'])
                return False
            if post['parent_author'] in self.config['whitelist']:
                self.log.info('White list match: ignore the report for %s' % post['parent_author'])
                return False
        return True

    def save_to_db(self, post):
        if post['signal_type']  == 'spam':
            result = self.db.store_report(post)
        elif post['signal_type'] == 'praise']:
            result = self.db.store_praise(post)
        return result

    def process_post(self, post):
        if post['signal_type'] == 'spam':
            post['reported_count'] = self.db.get_reported_count(post['parent_author'])
            self.posters.popleft().leave_warning(post)
        elif post['signal_type'] == 'praise':
            self.posters.popleft().leave_praise(post)
        else:
            pass

    async def work(self):
        self.log.info('Start Bot')
        loop = asyncio.get_event_loop()
        while self.run_flag:
            # Poll the queue every second
            await asyncio.sleep(1)
            while len(self.queue):
                if self.posters:
                    post = self.queue.popleft()
                    try:
                        self.log.info('%s reported %s' % (post['author'], post['parent_author']))
                        if not self.is_valid(post):
                            self.log.info('not valid')
                            break
                        if not self.save_to_db(post):
                            self.log.info('failed to save')
                            break
                        # Dispatch the past to the idle poster
                        self.process_post(post)
                    except Exception as e:
                        self.log.info('Error! %s' % e)
                        pass
                else:
                    self.log.info("No idle poster. Queue length=%s" % len(self.queue))
                    break
        self.feed.stop()

    def run(self):
        self.feed.start()
        return self.loop.run_until_complete(self.work())

    def stop(self):
        self.log.info('Stopping Bot')
        self.run_flag = False
        self.feed.stop()