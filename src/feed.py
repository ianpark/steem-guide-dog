"""
Feed
"""

import asyncio
import logging
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from steem.blockchain import Blockchain
from steem.post import Post


class Feed:
    log = logging.getLogger(__name__)
    """ Feed """
    def __init__(self, config, sink):
        self.config = config
        self.sink = sink
        self.blockchain = Blockchain()
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.instance = None
        self.run = False

    def check_signal(self, plain_post):
        # Check signals in the body
        for signal in self.config['signals']:
            # Match the first signal only
            if signal in plain_post.get('body',''):
                return signal
        return None

    def handle_data(self, plain_post):
        # Skip long comments
        if len(plain_post.get('body','')) > 256:
            return
        # Skip comments with no signal
        signal_found = self.check_signal(plain_post)
        if not signal_found:
            return
        post = Post(plain_post)
        post['bot_signal'] = signal_found
        # Skip comments of which depth is not 1
        if post.get('depth', 0) != 1:
            return
        
        post['parent_post_id'] = '@%s/%s' % (
                post['parent_author'], post['parent_permlink'])
        try:
            parent_post = Post(post['parent_post_id'])
        except:
            return

        tags = parent_post.json_metadata.get('tags')
        if tags and self.config['main_tag'] in tags or \
            any(x.startswith(self.config['tag_prefix']) for x in tags):
            self.sink(post)

    def work(self):
        self.log.info ('Start Feed')
        stream = self.blockchain.stream(filter_by=['comment'])
        while self.run:
            plain_post = next(stream)
            if not plain_post.get('parent_author', ''):
                continue
            if plain_post.get('parent_permlink', '').startswith('re-'):
                continue
            try:
                self.handle_data(plain_post)
            except Exception as e:
                self.log.info(e)
                self.log.info ("ERROR - %s" % e)
        self.log.info ('End Feed')

    def start(self):
        if not self.instance:
            self.run = True
            self.instance = self.executor.submit(self.work)
        else:
            raise Exception('Already running')

    def stop(self):
        self.log.info ('Stopping Feed')
        self.run = False
        self.instance.result()
        self.instance = None