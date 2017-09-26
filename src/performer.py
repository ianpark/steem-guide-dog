import logging
import random
import time 
from datetime import datetime, timedelta
from steem import Steem
from steem.post import Post

POSTING_GUARD_TIME = timedelta(seconds=20)

class Performer:
    log = logging.getLogger(__name__)
    def __init__(self, config, poster, priv_keys, on_complete):
        self.config = config
        self.poster = poster
        self.on_complete = on_complete
        self.steem = Steem(keys=priv_keys)
        self.last_posting = datetime.now() - POSTING_GUARD_TIME
        self.read_message_files()

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
            my_comment = self.steem.commit.post(
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
                self_vote=False
            )
            time.sleep(2)
            try:
                power = 100
                if self.steem.get_account('krguidedog')['voting_power'] < 5000:
                    power = 50
                my_comment = my_comment['operations'][0][1]
                post_id = '@%s/%s' % (my_comment['author'], my_comment['permlink'])
                self.steem.commit.vote(post_id, power, self.poster['account'])
            except:
                self.log.info('Failed to upvote!')
        except Exception as e:
            self.log.info(e)
            result = False
            
        self.on_complete({'result': result, 'wait_for': 20,
                'poster': self,
                'post': post})

    def generate_praise_message(self, post):
        rt = ['멋진', '섹시한', '훈훈한', '시크한', '알흠다운', '황홀한', '끝내주는', '요염한',
        '흥분되는', '짱재밌는', '잊지못할', '감동적인', '배꼽잡는', '러블리한', '쏘쿨한']
        if post['bot_signal'] == '@칭찬해':
            msg = ('%s @%s님 안녕하세요! %s @%s님 소개로 왔어요. 칭찬이 아주 자자 하시더라구요!! '
                    '%s 글 올려주신것 너무 감사해요. 작은 선물로 0.2 SBD를 보내드립니다 ^^'
                    % (random.choice(rt),
                    post['parent_author'],
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        elif post['bot_signal'] == '@축하해':
            msg = ('%s @%s님 안녕하세요! %s @%s님이 그러는데 정말 %s 일이 있으시다고 하더라구요!! '
                    '기분좋은 날 맛좋은 개껌 하나 사드시라고 0.2 SBD를 보내드립니다 ^^'
                    % (random.choice(rt),
                    post['parent_author'],
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        elif post['bot_signal'] == '@감사해':
            msg = ('%s @%s님 안녕하세요! %s @%s님이 너무너무 고마워 하셔서 저도 같이 감사드리려고 이렇게 왔어요!! '
                    '%s 하루 보내시라고 0.2 SBD를 보내드립니다 ^^'
                    % (random.choice(rt),
                    post['parent_author'],
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        msg = ('<table><tr><td>%s</td><td>%s</td></tr></table>'
                % (random.choice(self.poster['praise_photo']), msg))
        return msg

    def leave_praise(self, post):
        self.log.info("ID: %s, %s (%s)" % (post['identifier'], post, post['bot_signal']))
        result = True
        try:
            my_comment = self.steem.commit.post(
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
            time.sleep(2)
            # upvote for promotion
            try:
                my_comment = my_comment['operations'][0][1]
                post_id = '@%s/%s' % (my_comment['author'], my_comment['permlink'])
                self.steem.commit.vote(post_id, 20, self.poster['account'])
            except:
                self.log.info('Failed to upvote!')
            time.sleep(2)
            try:
                memo = '@%s 님께서 가이드독 활동을 통해 모은 포인트로 감사의 표시를 하였습니다. 해당 글을 확인해 주세요! https://steemit.com/%s' % (post['author'], post['parent_post_id'])
                self.steem.commit.transfer(
                    to=post['parent_author'],
                    amount=0.2,
                    asset='SBD',
                    account=self.poster['account'],
                    memo=memo)
            except:
                self.log.info('Failed to transfer 0.2 to %s!' % post['parent_author'])

        except Exception as e:
            self.log.info(e)
            result = False        
        self.on_complete({'result': result, 'wait_for': 20,
                'poster': self,
                'post': post})
    def send_no_point_alarm(self, post):
        try:
            memo = '가이드독 포인트가 부족합니다. 스팸글 신고를 통해 포인트를 쌓아주세요. 자세한 정보는 저의 계정을 방문하셔서 최신 글을 읽어주세요.'
            self.steem.commit.transfer(
                to=post['author'],
                amount=0.001,
                asset='SBD',
                account=self.poster['account'],
                memo=memo)
        except Exception as e:
            self.log.info(e)
        self.on_complete({'result': True, 'wait_for': 1,
                'poster': self,
                'post': post})
