import os
import logging
import random
import time 
import json
from datetime import datetime, timedelta
from steem import Steem
from steem.post import Post

class GuideDog:
    log = logging.getLogger(__name__)
    def __init__(self, config, db):
        self.config = config
        self.db = db
        keypath = os.path.expanduser(self.config['keyfile_path'])
        with open(keypath) as keyfile:    
            keyfile_json = json.load(keyfile)
            self.steem = Steem(keys=keyfile_json['krguidedog'])
        with open(self.config['guidedog']['message_file']) as f:
            message = f.readlines()
            self.message = [x.strip() for x in message]

    def create_post(self, post_id, body):
        return self.steem.commit.post(
                title='guide puppy',
                body=body,
                author=self.config['guidedog']['account'],
                permlink=None,
                reply_identifier=post_id,
                json_metadata=None,
                comment_options=None,
                community=None,
                tags=None,
                beneficiaries=None,
                self_vote=False
            )

    def vote(self, post_id, power, voter):
        try:
            self.steem.commit.vote(post_id, power, voter)
            self.log.info('Voted %s on %s' % (power, post_id))
        except Exception as e:
            self.log.info(e)
            raise


    def transfer(self, send_to, amount, memo):
        try:
            self.steem.commit.transfer(
                to=send_to,
                amount=amount,
                asset='SBD',
                account=self.config['guidedog']['account'],
                memo=memo)
            self.log.info('Transferred %s to %s: %s' % (amount, send_to, memo))
        except Exception as e:
            self.log.info(e)
            raise


    def work(self):
        self.log.info('Guide dog is working hard :-)')
        data = self.db.queue_get('post')
        if data:
            try:
                self.handle_post(data['data'])
                self.db.queue_finish('post', data)
            except Exception as e:
                self.log.error('Failed: post (will retry)')
                self.log.error(data)
                self.log.error(e)

        data = self.db.queue_get('vote')
        if data:
            try:
                self.log.info(data)
                voting = data['data']
                self.vote(voting['post_id'], voting['power'], voting['voter'])
                self.db.queue_finish('vote', data)
            except Exception as e:
                self.log.error('Failed: vote (will retry)')
                self.log.error(data)
                self.log.error(e)

        data = self.db.queue_get('transfer')
        if data:
            try:
                transfer = data['data']
                self.transfer(transfer['send_to'], transfer['amount'], transfer['memo'])
                self.db.queue_finish('transfer', data)
            except Exception as e:
                self.log.error('Failed: transfer (will retry)')
                self.log.error(data)
                self.log.error(e)

    def handle_post(self, post):
        self.log.info("ID: %s (%s)" % (post, post['bot_signal']))
        self.log.info ("%s/%s > %s" %(post['parent_author'], post['author'], post['body']))
        
        if self.db.is_reported(post):
            self.log.info('Skip duplicated report: %s', post)
            return

        if post['signal_type'] == 'spam':
            post['reported_count'] = self.db.get_reported_count(post['parent_author'])
            self.process_spam(post)
        elif post['signal_type'] == 'praise':
            point = self.db.get_usable_point(post['author'])
            self.log.info('Praise request - user: %s point: %s' % (post['author'], point ))
            if point >= 1:
                post['consume_point'] = 1
                self.leave_praise(post)
            else:
                self.log.info('Not enough point! %s %s' % (post['author'], point))
                self.send_no_point_alarm(post)
        else:
            pass

    def generate_warning_message(self,post):
        greet = ('Nice to meet you!' if post['reported_count'] <= 1
                else 'We have met %s times already!' % post['reported_count'])
        lines = [random.choice(self.config['guidedog']['photo']),
                '## Woff, woff!',
                '#### Hello @%s, %s' % (post['parent_author'], greet)
                ]
        lines.extend(self.message)
        return '\n'.join(lines)

    def process_spam(self, post):
        my_comment = self.create_post(post['parent_post_id'], self.generate_warning_message(post))
        self.db.store_report(post)
        # Push voting to the queue
        power = 100
        if self.steem.get_account('krguidedog')['voting_power'] < 5000:
            power = 50
        my_comment = my_comment['operations'][0][1]
        post_id = '@%s/%s' % (my_comment['author'], my_comment['permlink'])
        self.db.queue_push('vote', {'power': power, 'post_id': post_id, 'voter': self.config['guidedog']['account']})

    def generate_praise_message(self, post):
        rt = ['멋진', '섹시한', '훈훈한', '시크한', '알흠다운', '황홀한', '끝내주는', '요염한',
        '흥분되는', '짱재밌는', '잊지못할', '감동적인', '배꼽잡는', '러블리한', '쏘쿨한']
        pet = random.choice(self.config['guidedog']['praise_photo'])
        if post['bot_signal'] == '@칭찬해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님 소개로 왔어요. 칭찬이 아주 자자 하시더라구요!! '
                    '%s 글 올려주신것 너무 감사해요. 작은 선물로 0.2 SBD를 보내드립니다 ^^'
                    % ( 
                    random.choice(rt),
                    post['parent_author'],
                    pet[0],
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        elif post['bot_signal'] == '@축하해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 그러는데 정말 %s 일이 있으시다고 하더라구요!! '
                    '정말 축하드려요!! 기분좋은 날 맛좋은 개껌 하나 사드시라고 0.2 SBD를 보내드립니다 ^^'
                    % (
                    random.choice(rt),
                    post['parent_author'],
                    pet[0], 
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        elif post['bot_signal'] == '@감사해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 너무너무 고마워 하셔서 저도 같이 감사드리려고 이렇게 왔어요!! '
                    '%s 하루 보내시라고 0.2 SBD를 보내드립니다 ^^'
                    % (
                    random.choice(rt),
                    post['parent_author'],
                    pet[0], 
                    random.choice(rt),
                    post['author'],
                    random.choice(rt)))
        msg = ('<table><tr><td>%s</td><td>%s</td></tr></table>'
                % (pet[1], msg))
        return msg

    def leave_praise(self, post):
        my_comment = self.create_post(post['parent_post_id'], self.generate_praise_message(post))
        self.db.store_praise(post)
        # Push vote to queue
        my_comment = my_comment['operations'][0][1]
        post_id = '@%s/%s' % (my_comment['author'], my_comment['permlink'])
        self.db.queue_push('vote', {'power': 20, 'post_id': post_id, 'voter': self.config['guidedog']['account']})
        # Push transfer to queue
        self.db.queue_push('transfer', {'send_to': post['parent_author'],
            'amount': 0.2,
            'memo': '@%s 님께서 가이드독 활동을 통해 모은 포인트로 감사의 표시를 하였습니다.'
            '해당 글을 확인해 주세요! https://steemit.com/%s' % (post['author'], post['parent_post_id']) })

    def send_no_point_alarm(self, post):
        memo = '가이드독 포인트가 부족합니다. 스팸글 신고를 통해 포인트를 쌓아주세요. 자세한 정보는 저의 계정을 방문하셔서 최신 글을 읽어주세요.'
        self.db.queue_push('transfer', {'send_to': post['author'], 'amount': 0.001, 'memo': memo})
