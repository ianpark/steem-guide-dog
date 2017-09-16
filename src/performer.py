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

    def read_message_files(self):
        with open(self.poster['message_file']) as f:
            message = f.readlines()
            self.message = [x.strip() for x in message]

    def is_busy(self):
        if (datetime.now() - self.last_posting) < POSTING_GUARD_TIME:
            return False
        return True

    def generate_warning_message(self,post):
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
                body=self.generate_warning_message(post),
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

    def generate_praise_message(self, post):
        rt = ['멋진', '섹시한', '훈훈한', '시크한', '요염한', '지루한', '질척거리는', '흥분되는', '난처한',
            '음흉한', '흥겨운', '잊지못할', '으리으리한', '감동적인', '놀라운', '슬픈', '배꼽잡는', '러블리한']
        lines = [random.choice(self.poster['photo']),
                '%s @%s님 안녕하세요! %s @%s님 소개로 왔어요. 멍멍!' % (random.choice(rt), random.choice(rt), post['parent_author'], post['author']),
                '저는 스팸 없는 세상을 꿈꾸는 kr 가이드독이에요.'
                '좋은 글 올려주신것 너무 감사해요. 정말 %s 글이네요!' % (random.choice(rt)),
                '작지만 찐한 풀보팅 올리고 갑니다! 멍멍!'
                ]
        return '\n'.join(lines)

    def leave_praise(self, post):
        self.log.info("ID: %s, %s (%s)" % (post['identifier'], post, post['bot_signal']))
        result = True
        try:
            self.steem.commit.post(
                title='guide puppy',
                body=self.generate_praise_message(post),
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