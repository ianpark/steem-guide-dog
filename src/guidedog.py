import os
import uuid
import logging
import random
import time 
import json
import math
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
        with open(self.config['guidedog']['copyright_file']) as f:
            message = f.readlines()
            self.copyright = [x.strip() for x in message]
        self.last_daily_report = None
        self.daily_report_generator = Publisher(self.db)
        self.daily_report_timestamp = None

    def reputation(self, number, precision=2):
        rep = int(number)
        if rep == 0:
            return 25
        score = max([math.log10(abs(rep)) - 9, 0]) * 9 + 25
        if rep < 0:
            score = 50 - score
        return round(score, precision)

    def create_post(self, post_id, body, author='krguidedog'):
        comment = self.steem.commit.post(
                title='',
                body=body,
                author=author,
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
        try:
          if self.steem.get_account('asbear')['voting_power'] > 9000:
            comment = self.steem.commit.post(
                 title='guidedog public fund',
                 body="guidedog antispam service: public fund raising for spam reporters",
                 author=self.config['guidedog']['account'],
                 permlink=None,
                 reply_identifier=sys_random.choice(["@krguidedog/kr-2017-8-31",
                                                   "@krguidedog/kr-2017-9-1",
                                                   "@krguidedog/kr-2017-9-2",
                                                   "@krguidedog/kr-2017-9-3",
                                                   "@krguidedog/kr-2017-9-4",
                                                   "@krguidedog/kr-2017-9-5",
                                                   "@krguidedog/kr-2017-9-6",
                                                   "@krguidedog/kr-2017-9-7"]),
                 json_metadata=None,
                 comment_options=None,
                 community=None,
                 tags=None,
                 beneficiaries=None,
                 self_vote=False
            )
            self.log.info('Staking vote..')
            post = comment['operations'][0][1]
            post_id = '@%s/%s' % (post['author'], post['permlink'])
            self.steem.commit.vote(post_id, 100, 'asbear')
        except Exception as e:
            self.log.info('Staking failed' + str(e))
            pass

    def vote(self, post_id, power, voter):
        try:
            self.steem.commit.vote(post_id, power, voter)
            self.log.info('%s voted on %s with %s percentage' % (voter, post_id, power))
        except Exception as e:
            self.log.info("Failed to vote: " + str(e))
            pass

    def transfer(self, send_to, amount, memo):
        try:
            self.steem.commit.transfer(
                to=send_to,
                amount=amount,
                asset='STEEM',
                account=self.config['guidedog']['account'],
                memo=memo)
            self.log.info('Transferred %s to %s: %s' % (amount, send_to, memo))
        except Exception as e:
            self.log.info("Failed to transfer: " + str(e))
            raise

    def resteem(self, post_id, resteemer):
        try:
            self.steem.commit.resteem(post_id, resteemer)
            self.log.info('Resteemed %s by %s' % (post_id, resteemer))
        except Exception as e:
            self.log.info("Failed to resteem: " + str(e))
            pass

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
                comment_options = {
                    'max_accepted_payout': '0.000 SBD',
                    'percent_steem_dollars': 0,
                    'allow_votes': True,
                    'allow_curation_rewards': True,
                    'extensions': []
                }
                comment = self.steem.commit.post(
                    title=result['title'],
                    body=result['body'],
                    author='asbear',
                    permlink=str(uuid.uuid4()),
                    reply_identifier=None,
                    json_metadata=None,
                    comment_options=comment_options,
                    community=None,
                    tags='kr krguidedog antispam',
                    beneficiaries=None,
                    self_vote=False)

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

        data = self.db.queue_get('resteem')
        if data:
            try:
                resteem = data['data']
                self.resteem(resteem['post_id'], resteem['resteemer'])
                self.db.queue_finish('resteem', data)
            except Exception as e:
                self.log.error('Failed: resteem (will retry)')
                self.log.error(data)
                self.log.error(e)

        self.daily_report()
        # Prevent wasting the donated funds
        # self.try_staking()

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
            if post['author'] in self.config["praise_curator"]:
                self.leave_praise(post)
            elif point >= 1:
                self.leave_praise(post)
                self.db.use_point(post['author'], 1)
            else:
                self.log.info('Not enough point! %s %s' % (post['author'], point))
                self.send_no_point_alarm(post)
        elif post['signal_type'] == 'promote':
            if self.db.is_promoted(post):
                self.log.info('Skip request: already promoted')
                return

            point = self.db.get_usable_point(post['author'])
            self.log.info('Promote request - user: %s point: %s' % (post['author'], point ))
            if post['author'] in self.config["promote_curator"]:
                self.promote(post)
            elif point >= 1:
                self.promote(post)
                self.db.use_point(post['author'], 1)
            else:
                self.log.info('Not enough point! %s %s' % (post['author'], point))
                self.send_no_point_alarm(post)
        elif post['signal_type'] == 'welcome':
            if post['author'] not in self.config["welcome_curator"]:
                self.log.info('Skip request: Not allowed user')
            if self.db.is_welcomed(post):
                self.log.info('Skip request: already welcomed')
                return
            rep = self.reputation(self.steem.get_account(post['parent_author'])['reputation'])
            if rep > 50:
                self.log.info('Skip request: reputation is too high (%s, %s) ' % (post['parent_author'], rep))
                return
            self.log.info('Welcome %s (%s)!' % (post['parent_author'], rep))
            self.welcome(post)
        else:
            pass

    def generate_warning_message(self,post):
        if post['bot_signal'] == "@저작권안내":
            greet = ('저작권 안내입니다.' if post['reported_count'] <= 1
                    else '%s 번째 안내입니다.' % post['reported_count'])
            lines = ['https://i.imgur.com/2PPRCJq.png',
                    '#### 안녕하세요 @%s님, %s' % (post['parent_author'], greet)
                    ]
            lines.extend(self.copyright)
            return '\n'.join(lines)
        else:
            greet = ('Nice to meet you!' if post['reported_count'] <= 1
                    else 'We have met %s times already!' % post['reported_count'])
            lines = [sys_random.choice(self.config['guidedog']['photo']),
                    '## Woff, woff!',
                    '#### Hello @%s, %s' % (post['parent_author'], greet)
                    ]
            lines.extend(self.message)
            return '\n'.join(lines)

    def vote_on_post(self, post, supporters):
        post = post['operations'][0][1]
        self.supporters_vote(post['author'], post['permlink'], supporters)

    def supporters_vote(self, author, permlink, supporters):
        votes = self.steem.get_active_votes(author, permlink)
        voters = set()
        for vote in votes:
            voters.add(vote['voter'])

        for supporter in supporters:
            # Skip already voted supporters
            if not supporter['account'] in voters:
                voting_power = self.steem.get_account(supporter['account'])['voting_power']
                if voting_power >  supporter['voteOver']:
                    self.db.queue_push(
                        'vote',
                        {'power': supporter['weight'],
                        'post_id': '@%s/%s' % (author, permlink),
                        'voter': supporter['account'] })
            else:
                self.log.info('%s already voted' % supporter)

    def process_spam(self, post):
        my_comment = self.create_post(post['parent_post_id'], self.generate_warning_message(post))
        self.db.store_report(post)
        self.vote_on_post(my_comment, self.config['spam_supporters'])

    def generate_benefit_message(self, post):
        reward = "0.6 STEEM"
        rt = ['멋진', '섹시한', '훈훈한', '시크한', '알흠다운', '황홀한', '끝내주는', '요염한',
        '흥분되는', '짱재밌는', '잊지못할', '감동적인', '배꼽잡는', '러블리한', '쏘쿨한', '분위기있는']
        pet = sys_random.choice(self.config['guidedog']['pets'])
        pet_name = '<a href="/%s">%s</a>' % (pet['parent'], pet['name'])
        pet_photo = sys_random.choice(pet['photo'])
        if post['bot_signal'] == '@칭찬해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님 소개로 왔어요. 칭찬이 아주 자자 하시더라구요!! '
                    '%s 글 올려주신것 너무 감사해요. 작은 선물로 %s를 보내드립니다 ^^'
                    % ( 
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt),
                    reward))
        elif post['bot_signal'] == '@축하해':
            msg = (('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 그러는데 정말 %s 일이 있으시다고 하더라구요!! '
                    '정말 축하드려요!! 기분좋은 날 맛좋은 '+ sys_random.choice(['개껌 하나', '개밥 한그릇', '개뼈다구 하나']) +' 사드시라고 %s를 보내드립니다 ^^')
                    % (
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt),
                    reward))
        elif post['bot_signal'] == '@감사해':
            msg = ('%s @%s님 안녕하세요! %s 입니다. %s @%s님이 너무너무 고마워 하셔서 저도 같이 감사드리려고 이렇게 왔어요!! '
                    '%s 하루 보내시라고 %s를 보내드립니다 ^^'
                    % (
                    sys_random.choice(rt),
                    post['parent_author'],
                    pet_name,
                    sys_random.choice(rt),
                    post['author'],
                    sys_random.choice(rt),
                    reward))
        elif post['bot_signal'] == '@위로해':
            msg = (('@%s님 안녕하세요. %s 입니다. @%s께 이야기 다 들었습니다. ' +
                   sys_random.choice(['세상사 다 그런것 아닐까요?. ', '인생지사 새옹지마라고 하잖아요. ']) +
                   '힘든일이 있으면 반드시 좋은일도 있대요! 기운 내시라고 %s를 보내드립니다.')
                    % (
                    post['parent_author'],
                    pet_name,
                    post['author'],
                    reward))
        elif post['bot_signal'] == '@홍보해':
            msg = (('@%s님 안녕하세요. %s 입니다. @%s님이 이 글을 너무 좋아하셔서, 저에게 홍보를 부탁 하셨습니다.' +
                    ' 이 글은 @krguidedog에 의하여 리스팀 되었으며, 가이드독 서포터들로부터 보팅을 받으셨습니다. 축하드립니다!')
                    % (
                    post['parent_author'],
                    pet_name,
                    post['author'],
                    ))
        msg = ('<table><tr><td>%s</td><td>%s</td></tr></table>'
                % (pet_photo, msg))
        return msg

    def leave_praise(self, post):
        my_comment = self.create_post(post['parent_post_id'], self.generate_benefit_message(post))
        self.db.store_praise(post)
        self.vote_on_post(my_comment, self.config['praise_supporters'])

        # Push transfer to queue
        self.db.queue_push('transfer', {'send_to': post['parent_author'],
            'amount': 0.6,
            'memo': '@%s 님께서 가이드독 활동을 통해 모은 포인트로 감사의 표시를 하였습니다.'
            '해당 글을 확인해 주세요! https://steemit.com/%s' % (post['author'], post['parent_post_id']) })

    def promote(self, post):
        my_comment = self.create_post(post['parent_post_id'], self.generate_benefit_message(post))
        self.db.store_promote(post)
        self.vote_on_post(my_comment, self.config['praise_supporters'])
        self.db.queue_push('resteem', {'post_id': post['parent_post_id'], 'resteemer': self.config['guidedog']['account']})
        self.supporters_vote(post['parent_author'], post['parent_permlink'], self.config['promotion_supporters'])

    def welcome(self, post):
        # Message
        message = [
            "## @%s님 스팀잇에 오신것을 환영합니다!" % post['parent_author'],
            "스팀잇 정착을 도와드리기 위하여 @%s님의 부탁을 받고 찾아온 @easysteemit 입니다. 힘찬 출발을 응원하는 의미에서 @easysteemit 서포터 보팅을 해드립니다. 그리고 더 많은 분들에게 소개해 드리기 위해서 @krguidedog을 통해 @홍보해 드립니다." % post['author'],
            "",
            "### [이지스팀잇]",
            "스팀잇은 처음에는 낮설고 잡해 보이지만, 필요한 것들을 하나하나 익히시고 나면 편리하고 즐겁게 즐기실 수 있어요. 이지스팀잇은 스팀잇을 사랑하는 분들이 마음을 한데 모아서 만든 스팀잇 안내서입니다. 스팀잇을 새로 시작하는 분들이 스팀잇을 더욱 편하게 접할 수 있도록 도와드릴것입니다.",
            "",
            "<a href='/@easysteemit'><img src='https://steemitimages.com/300x0/https://steemitimages.com/DQmZmqw2L61Rrnvy92WAH5xSnn3Ud1ZcMJWWFcff141DPqV/daemoon.png'></a>"
        ]
        # Process
        my_comment = self.create_post(post['parent_post_id'], '\n'.join(message), 'easysteemit')
        self.db.store_welcome(post)
        self.supporters_vote(post['parent_author'], post['parent_permlink'], self.config['welcome_supporters'])

    def send_no_point_alarm(self, post):
        memo = '가이드독 포인트가 부족합니다. 스팸글 신고를 통해 포인트를 쌓아주세요. 자세한 정보는 다음 링크에서 확인해 주세요. https://steemit.com/kr/@asbear/33kqka-kr'
        self.db.queue_push('transfer', {'send_to': post['author'], 'amount': 0.001, 'memo': memo})
