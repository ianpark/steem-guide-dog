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

    def is_busy(self):
        if (datetime.now() - self.last_posting) < POSTING_GUARD_TIME:
            return False
        return True

    def generate_message(self,post):
        greet = ('Nice to meet you!'if post['reported_count'] <= 1 
                else 'We have met %s times already!' % post['reported_count'])
        lines = [random.choice(self.poster['photo']),
                '## Hello @%s! %s' % (post['parent_author'], greet),
                'I am just a tiny guide puppy who is eager to help you to communicate well with the friends in KR community. Metting me means that **your post needs to be improved** in certain ways to be welcomed by the Korean readers. Please see my advice below :)',
                '',
                '- Please **refrain using any online translators**. It does not work well with Korean language. English is preferred than translated Korean.',
                '- It is ok to use English, but the post **should be somewhat relevant to Korean**.',
                '- **Do not copy someone else\'s content**. You will be purnished and banned by the Korean whales if you do.',
                '- If you meet me very often, you would be put into the **blacklist**.',
                '',
                'I hope you enjoy Steemit as much as we do. :)',
                '',
                'Many thanks!']
        return '\n'.join(lines)

    def leave_comment(self, post):
        self.log.info("ID: %s, %s (%s)" % (post['identifier'], post, post['bot_signal']))
        self.log.info ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))
        self.log.info (self.generate_message(post))
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
        except Exception as e:
            self.log.info(e)
            result = False
            
        self.on_complete({'result': True,
                'poster': self,
                'post': post})

