"""
Bot
"""

import asyncio
import json
import logging
import os

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from data import Data
from feed import Feed
from performer import Performer
from guidedog import GuideDog
from datetime import datetime
from db import DataStore
from collections import deque
from webapp import run_webapp


CONFIG_FILE_PATH = 'etc/config.json'

class Bot:
    executor = ThreadPoolExecutor(max_workers=8)
    log = logging.getLogger(__name__)
    def __init__(self):
        with open(CONFIG_FILE_PATH) as config:    
            self.config = json.load(config)
        self.loop = asyncio.get_event_loop()
        self.queue = deque()
        self.posters = deque()
        self.db = DataStore()
        self.feed = Feed(self.config, self.db)
        self.guidedog = GuideDog(self.config, self.db)
        self.data = Data()
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
        self.refresh_data_cache()
        # self.executor.submit(run_webapp, self.config, self.data)
    
    def refresh_data_cache(self):
        # Update the data storage
        self.data.reports = self.db.read_all(datetime.now().timestamp() - 60 * 60 * 72)
        self.data.users = self.db.get_all_user()

    def on_complete(self, result):
        self.log.info('Finished: %s' % result)
        self.loop.call_later(result.get('wait_for', 20), self.posters.append, result['poster'])
        if not result['result']:
            self.log.info('Append data to the left: %s' % result['post'] )
            self.queue.appendleft(result['post'])
        else:
            # Use point
            author = result['post']['author']
            used_point = result['post'].get('consume_point', 0)
            if used_point:
                self.db.use_point(author, used_point)
            # Refresh data cache
            self.refresh_data_cache()

    async def work(self):
        self.log.info('Start Bot')
        loop = asyncio.get_event_loop()
        while self.run_flag:
            # Poll the queue every second
            await asyncio.sleep(2)
            self.guidedog.work()
        self.feed.stop()

    def run(self):
        self.feed.start()
        return self.loop.run_until_complete(self.work())

    def stop(self):
        self.log.info('Stopping Bot')
        self.run_flag = False
        self.feed.stop()
