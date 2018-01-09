"""
Feed
"""

import asyncio
import logging
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from steem.blockchain import Blockchain
from steem.post import Post
from block_pointer import BlockPointer
from steem.steemd import Steemd
from steem import Steem


class PostStream:
    log = logging.getLogger(__name__)
    last_shown_no = 0
    def __init__(self, block_pointer):
        self.bp = block_pointer
        self.start_stream()
        self.steem = Steem()

    def start_stream(self):
        self.log.info('Start new block chain and stream %s' % self.bp.last())

    def get(self):
        try:
            block = self.steem.get_block(self.bp.last())
            if block == None:
                return None
            output = []
            for trans in block['transactions']:
                if trans['operations'][0][0] == 'comment':
                    post = trans['operations'][0][1]
                    post['block_num'] = self.bp.last()
                    post['timestamp'] = trans['expiration']
                    output.append(post)
            if self.bp.last() > (self.last_shown_no + 100):
                self.last_shown_no = self.bp.last()
                self.log.info('Processing block: %s' % self.last_shown_no)
            self.bp.update(self.bp.last() + 1)
            return output
        except Exception as e:
            self.log.error('Failed receiving from the stream: ' + str(e))
            raise

class Feed:
    log = logging.getLogger(__name__)
    """ Feed """
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.blockchain = Blockchain()
        self.loop = asyncio.get_event_loop()
        self.ps = PostStream(BlockPointer())
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.instance = None
        self.run = False

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

    def work(self):
        self.log.info ('Start Feed')
        while self.run:
            try:
                trans = self.ps.get()
                if trans == None:
                    # No block is created yet
                    sleep(1)
                    continue
                for plain_post in trans:
                    if not plain_post.get('parent_author', ''):
                        continue
                    if plain_post.get('parent_permlink', '').startswith('re-'):
                        continue
                    self.handle_data(plain_post)
            except Exception as e:
                self.log.error("Failed collecting and processing the post")
                self.log.error(e)
                sleep(1)
        self.log.info ('End Feed')

    def check_signal(self, plain_post):
        # Check signals in the body
        for signal in self.config['report_signals'] + self.config['praise_signals'] + self.config['promote_signals']:
            # Match the first signal only
            if signal in plain_post.get('body',''):
                return signal
        return None

    def is_valid(self, post):
        if post['signal_type'] == 'praise' or post['signal_type'] == 'promote':
            # Block self praise or self promotion
            if post['author'] == post['parent_author']:
                self.log.info('Author and parent author is the same')
                return False
            if post['author'] in self.config['blacklist']:
                self.log.info('Black list match: ignore the report from %s' % post['author'])
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

    def handle_data(self, plain_post):
        # Skip long comments
        if len(plain_post.get('body','')) > 1024:
            return
        # Skip comments with no signal
        signal_found = self.check_signal(plain_post)
        if not signal_found:
            return
        post = Post(plain_post)
        # Skip comments of which depth is not 1
        if post.get('depth', 0) != 1:
            return
        parent_post_id = '@%s/%s' % (
                post['parent_author'], post['parent_permlink'])
        try:
            parent_post = Post(parent_post_id)
        except:
            self.log.error('Failed to get the parent post %s' % parent_post_id)
            return

        tags = parent_post.json_metadata.get('tags')
        if tags and self.config['main_tag'] in tags or \
            any(x.startswith(self.config['tag_prefix']) for x in tags):
            self.log.info('Found a matching comment: %s' % plain_post.get('body'))
            # Save signal
            plain_post['bot_signal'] = signal_found
            plain_post['parent_post_id']  = parent_post_id
            # Select signal type
            if plain_post['bot_signal'] in self.config['report_signals']:
                plain_post['signal_type'] = 'spam'
            elif plain_post['bot_signal'] in self.config['praise_signals']:
                plain_post['signal_type'] = 'praise'
            elif plain_post['bot_signal'] in self.config['promote_signals']:
                plain_post['signal_type'] = 'promote'
            else:
                plain_post['signal_type'] = 'unknown'
            if not self.is_valid(plain_post):
                self.log.info('Ignore not valid request')
                return
            # sink down
            self.db.queue_push('post', plain_post)
