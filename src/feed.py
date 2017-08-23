"""
Feed
"""

import asyncio
from time import sleep
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from steem.blockchain import Blockchain
from steem.post import Post

PREFIX = 'kr-guidedogtest'
SIGNALS = ['kr-guide-dog!', 'kr-guide-cat!']

class Feed:
    """ Feed """
    def __init__(self):
        self.blockchain = Blockchain()
        self.loop = asyncio.get_event_loop()
        self.q = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.instance = None
        self.run = False

    def handle_data(self, post):
        """ handle_data """
        tags = post.json_metadata.get('tags', [])
        if 'kr' in tags or any(x.startswith(PREFIX) for x in tags):
            for signal in SIGNALS:
                # Match the first signal only
                if signal in post.get('body',''):
                    post['bot-signal'] = signal
                    self.q.put_nowait(post)
                    break

    def work(self):
        stream = map(Post, self.blockchain.stream(filter_by=['comment']))
        while self.run:
            try:
                self.handle_data(next(stream))
            except Exception as e:
                print ("ERROR - %s" % e)


    def start(self):
        if not self.instance:
            self.run = True
            self.instance = self.executor.submit(self.work)
        else:
            raise Exception('Already running')

    def stop(self):
        self.run = False
        self.instance.result()
        self.instance = None

    async def get_feed(self):
        value = await self.q.get()
        return value