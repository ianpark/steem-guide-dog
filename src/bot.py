"""
Bot
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from feed import Feed
from performer import Performer

class Bot:
    def __init__(self, config):
        self.config = config
        self.loop = asyncio.get_event_loop()
        self.feed = Feed(self.config)
        self.performer = Performer(self.config)
    
    async def work(self):
        self.feed.start()
        loop = asyncio.get_event_loop()
        while True:
            await asyncio.sleep(1)
            while self.feed.q.qsize():
                post =  self.feed.q.get_nowait()
                self.performer.leave_comment(post)
        self.feed.stop()

    def run(self):
        return self.loop.run_until_complete(self.work())


# print ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))