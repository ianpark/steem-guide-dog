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

    async def work(self):
        print ('Start Bot')
        loop = asyncio.get_event_loop()
        while self.run_flag:
            # Poll the queue every second
            await asyncio.sleep(1)
            while len(self.queue):
                if self.posters:
                    poster = self.posters.popleft()
                    poster.leave_comment(self.queue.popleft())
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