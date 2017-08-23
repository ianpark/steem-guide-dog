"""
Bot
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from feed import Feed

class Bot:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.feed = Feed()
        pass
    
    async def work(self):
        self.feed.start()
        loop = asyncio.get_event_loop()
        while True:
            await asyncio.sleep(1)
            while self.feed.q.qsize():
                post =  self.feed.q.get_nowait()
                print("New: %s (%s)" % (post, post['bot-signal']))
                print ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))

        self.feed.stop()

    def run(self):
        return self.loop.run_until_complete(self.work())


# print ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))