"""
Feed
"""

import asyncio
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from steem.blockchain import Blockchain
from steem.post import Post


class Feed:
    """ Feed """
    def __init__(self, config, sink):
        self.config = config
        self.sink = sink
        self.blockchain = Blockchain()
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.instance = None
        self.run = False

    def handle_data(self, post):
        # weirdly non-comment posts are still being injected
        if not post.is_comment():
            return
        """ handle_data """
        tags = post.json_metadata.get('tags', [])
        if tags and self.config['main_tag'] in tags or \
            any(x.startswith(self.config['tag_prefix']) for x in tags):
            for signal in self.config['signals']:
                # Match the first signal only
                if signal in post.get('body',''):
                    post['bot-signal'] = signal
                    self.sink(post)
                    break

    def work(self):
        print ('Start Feed')
        stream = map(Post, self.blockchain.stream(filter_by=['comment']))
        while self.run:
            try:
                self.handle_data(next(stream))
            except Exception as e:
                print(e)
                print ("ERROR - %s" % e)


    def start(self):
        if not self.instance:
            self.run = True
            self.instance = self.executor.submit(self.work)
        else:
            raise Exception('Already running')

    def stop(self):
        print ('Stopping Feed')
        self.run = False
        self.instance.result()
        self.instance = None