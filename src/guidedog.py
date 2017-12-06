import os
import uuid
import logging
import random
import time 
import json
from datetime import datetime, timedelta
from steem import Steem
from steem.post import Post
from time import sleep
from publisher import Publisher

sys_random = random.SystemRandom()

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
        self.last_daily_report = None
        self.daily_report_generator = Publisher(self.db)
        self.daily_report_timestamp = None

    def create_post(self, post_id, body):
        comment = self.steem.commit.post(
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
        post_item = comment['operations'][0][1]
        post_id = '@%s/%s' % (post_item['author'], post_item['permlink'])

        limit = 3
        while True:
            sleep(1)
            try:
                double_check = Post(post_id)
                return comment
            except Exception as e:
                limit -= 1
                if limit == 0:
                    raise 'Posting check failure'

    def try_staking(self):
        if self.steem.get_account('krguidedog')['voting_power'] > 9000:
            self.steem.commit.post(
                title='guidedog training',
                body="guidedog antispam service",
                author=self.config['guidedog']['account'],
                permlink=None,
                reply_identifier=sys_random.choice(["@krguidedog/test-kr-guidedog-please-ignore",
                                                    "@krguidedog/test-kr-guidedog-please-ignore-2",
                                                    "@krguidedog/kr-guiddog-test",
                                                    "@krguidedog/test4",
                                                    "@krguidedog/test5",
                                                    "@krguidedog/test6"])
                json_metadata=None,
                comment_options=None,
                community=None,
                tags=None,
                beneficiaries=None,
                self_vote=True
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

    def daily_report(self):
        last_daily_report = None
        try:
            with open("db/daily_report", "r") as f:
                last_daily_report = f.read().splitlines()[0]
        except:
            self.log.info('Failed to read daily_report file!!')
            return
        try:
            theday = datetime.now() - timedelta(days=1)
            if last_daily_report == theday.strftime("%d %b %Y"):
                # Already created until the last available day
                return
            newday = datetime.strptime(last_daily_report, "%d %b %Y") + timedelta(days=1)
            result = self.daily_report_generator.generate_report(newday.strftime("%d %b %Y"))
            if result == None:
                self.log.info('No activiey is found in ' + newday.strftime("%d %b %Y"))
            else:
                self.log.info('Creating a daily report for ' + newday.strftime("%d %b %Y"))
                comment = self.steem.commit.post(
                    title=result['title'],
                    body=result['body'],
                    author='asbear',
                    permlink=str(uuid.uuid4()),
                    reply_identifier=None,
                    json_metadata=None,
                    comment_options=None,
                    community=None,
                    tags='kr krguidedog antispam',
                    beneficiaries=None,
                    self_vote=True)
                try:
                    post_item = comment['operations'][0][1]
                    post_id = '@%s/%s' % (post_item['author'], post_item['permlink'])
                    self.vote(post_id, 100, 'krguidedog')
                except:
                    pass

            # All succeeded. Update the last report day
            with open("db/daily_report", "w") as f:
                f.write(newday.strftime("%d %b %Y"))
            
        except Exception as e:
            self.log.info(e)
            self.log.info('Failed to create a daily report for ' + newday.strftime("%d %b %Y"))
            return

    def work(self):
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

        self.daily_report()
        # Prevent wasting the donated funds
        self.try_staking()

    def handle_post(self, post):
        self.log.info("New Command [%s -> %s -> %s] : %s" % (post['author'], post['bot_signal'], post['parent_author'], post))
        if post['signal_type'] == 'spam':
            if self.db.is_reported(post):
                self.log.info('Skip request: already reported')
                return
            post['reported_count'] = self.db.get_reported_count(post['parent_author'])
            self.process_spam(post)
        elif post['signal_type'] == 'praise':
            if self.db.is_already_consumed_comment(post):
                self.log.info('Skip request: already consumed comment')
                return
        
            point = self.db.get_usable_point(post['author'])
            self.log.info('Praise request - user: %s point: %s' % (post['author'], point ))
            if point >= 1:
                self.leave_praise(post)
                self.db.use_point(post['author'], 1)
            else:
                self.log.info('Not enough point! %s %s' % (post['author'], point))
                self.send_no_point_alarm(post)
        else:
            pass

    def generate_warning_message(self,post):
        greet = ('Nice to meet you!' if post['reported_count'] <= 1
                else 'We have met %s times already!' % post['reported_count'])
        lines = [sys_random.choice(self.config['guidedog']['photo']),
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
        '흥분되는', '짱재밌는', '잊지못할', '감동적인', '배꼽잡는', '러블리한', '쏘쿨한', '분위기있는']
        pet = sys_random.choice(self.config['guidedog']['pets'])
        pet_name = '<a href="/%s">%s</a>' % (pet['parent'], pet['name'])
        pet_photo = sys_random.choice(pet['photo'])
        if post['bot_signal'] == '@칭찬해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님 소개로 왔어요. 칭찬이 아주 자자 하시더라구요!! '
                    '%s 글 올려주신것 너무 감사해요. 작은 선물로 0.3 SBD를 보내드립니다 ^^'
                    % ( 
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt)))
        elif post['bot_signal'] == '@축하해':
            msg = (('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 그러는데 정말 %s 일이 있으시다고 하더라구요!! '
                    '정말 축하드려요!! 기분좋은 날 맛좋은 '+ sys_random.choice(['개껌 하나', '개밥 한그릇', '개뼈다구 하나']) +' 사드시라고 0.3 SBD를 보내드립니다 ^^')
                    % (
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt)))
        elif post['bot_signal'] == '@감사해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 너무너무 고마워 하셔서 저도 같이 감사드리려고 이렇게 왔어요!! '
                    '%s 하루 보내시라고 0.3 SBD를 보내드립니다 ^^'
                    % (
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt)))
        elif post['bot_signal'] == '@위로해':
            msg = (('@%s님 안녕하세요. %s 입니다. @%s께 이야기 다 들었습니다. ' +
                   sys_random.choice(['세상사 다 그런것 아닐까요?. ', '인생지사 새옹지마라고 하잖아요. ']) +
                   '힘든일이 있으면 반드시 좋은일도 있대요! 기운 내시라고 0.3 SBD를 보내드립니다.')
                    % (
                    post['parent_author'],
                    pet_name,
                    post['author']
                    ))
        msg = ('<table><tr><td>%s</td><td>%s</td></tr></table>'
                % (pet_photo, msg))
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
            'amount': 0.3,
            'memo': '@%s 님께서 가이드독 활동을 통해 모은 포인트로 감사의 표시를 하였습니다.'
            '해당 글을 확인해 주세요! https://steemit.com/%s' % (post['author'], post['parent_post_id']) })

    def send_no_point_alarm(self, post):
        memo = '가이드독 포인트가 부족합니다. 스팸글 신고를 통해 포인트를 쌓아주세요. 자세한 정보는 저의 계정을 방문하셔서 최신 글을 읽어주세요.'
        self.db.queue_push('transfer', {'send_to': post['author'], 'amount': 0.001, 'memo': memo})
