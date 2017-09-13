import logging
import random
from datetime import datetime, timedelta
from steem import Steem

POSTING_GUARD_TIME = timedelta(seconds=20)

class Performer:
    log = logging.getLogger(__name__)
    def __init__(self, config, poster, priv_keys, on_complete):
        self.config = config
        self.poster = poster
        self.on_complete = on_complete
        self.steem = Steem(keys=priv_keys)
        self.last_posting = datetime.now() - POSTING_GUARD_TIME

        with open(poster['message_file']) as f:
            message = f.readlines()
            self.message = [x.strip() for x in message]

    def is_busy(self):
        if (datetime.now() - self.last_posting) < POSTING_GUARD_TIME:
            return False
        return True

    def generate_message(self,post):
        greet = ('Nice to meet you!' if post['reported_count'] <= 1
                else 'We have met %s times already!' % post['reported_count'])
        lines = [random.choice(self.poster['photo']),
                '## Woff, woff!',
                '#### Hello @%s, %s' % (post['parent_author'], greet)
                ]
        lines.extend(self.message)
        return '\n'.join(lines)

    def process_warning(self, post):
        self.log.info("ID: %s, %s (%s)" % (post['identifier'], post, post['bot_signal']))
        self.log.info ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))
        result = True
        try:
            self.steem.commit.post(
                title='guide puppy',
                body=self.generate_message(post),
                author=self.poster['account'],
                permlink=None,
                reply_identifier=post['parent_post_id'],
                json_metadata=None,
                comment_options=None,
                community=None,
                tags=None,
                beneficiaries=None,
                self_vote=True
            )
        except Exception as e:
            self.log.info(e)
            result = False
            
        self.on_complete({'result': True,
                'poster': self,
                'post': post})

    def leave_praise(self, post):
        self.log.info("ID: %s, %s (%s)" % (post['identifier'], post, post['bot_signal']))
        result = True
        try:
            self.steem.commit.post(
                title='guide puppy',
                body=self.generate_message(post),
                author=self.poster['account'],
                permlink=None,
                reply_identifier=post['parent_post_id'],
                json_metadata=None,
                comment_options=None,
                community=None,
                tags=None,
                beneficiaries=None,
                self_vote=False
            )
            parent_post = Post(post['parent_post_id'])
            parent_post.upvote(10)
        except Exception as e:
            self.log.info(e)
            result = False        
        self.on_complete({'result': True,
                'poster': self,
                'post': post})