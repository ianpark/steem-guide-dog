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
        self.db = DataStore()
        self.feed = Feed(self.config, self.db)
        self.guideDog = GuideDog(self.config, self.db)
        self.run_flag = True

    async def work(self):
        self.log.info('Start Bot')
        loop = asyncio.get_event_loop()
        while self.run_flag:
            # Poll the queue every second
            await asyncio.sleep(3)
            self.guideDog.work()
        self.feed.stop()

    def run(self):
        self.feed.start()
        return self.loop.run_until_complete(self.work())

    def stop(self):
        self.log.info('Stopping Bot')
        self.run_flag = False
        self.feed.stop()
