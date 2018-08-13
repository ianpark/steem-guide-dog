import util
from datetime import datetime
from operator import itemgetter
from collections import Counter
from db import DataStore


class Publisher:
    def __init__(self, db=None):
        if db:
            self.db = db
        else:
            self.db = DataStore()
        pass
    
    def get_spammer_rank(self, records):
        counter = Counter(report['author'] for report in records)
        stat = []
        for key in counter:
            stat.append({'name': key,
                         'count': counter[key]})
        return sorted(stat, key=itemgetter('count'), reverse=True)

    def get_rank(self, records):
        counter = Counter(report['reporter'] for report in records)
        stat = []
        for key in counter:
            stat.append({'name': key,
                         'count': counter[key],
                         'stake': round(float(counter[key])/len(records), 3)})
        return sorted(stat, key=itemgetter('count'), reverse=True)


    def get_all_points(self):
        # collect all user 
        users = self.db.get_all_user()
        all_user = ['아이디 | 신고수 | 포인트(총/잔여)',
                    '--- | --- | ---']
        for user in users:
            remaining_point = user['point_earned'] - user['point_used']
            if remaining_point == 0:
                continue
            all_user.append(
                '@%s | %s | %s / %s' % (
                    user['user_id'],
                    user['report_count'],
                    user['point_earned'],
                    remaining_point
                )
            )
        return all_user

    def generate_report(self, start_date, end_date=None):
        if not end_date:
            end_date = start_date
        records = self.db.get_rank_period(start_date, end_date)
        if not records:
            return None
        start = util.get_kr_time_from_timestamp(records[0]['report_time'])
        end = util.get_kr_time_from_timestamp(records[-1]['report_time'])
        md = util.get_kr_time(records[0]['report_time']).strftime('%-m월 %-d일')
        period = start + (' - ' + end if start != end else '')
        medals = [
                "http://i.imgur.com/hv0zL8U.png",
                "http://i.imgur.com/xe9CD0S.png",
                "http://i.imgur.com/50zpz2p.png"
                ]
        reporter_rank = self.get_rank(records)

        reporter_table = ['불러주신분 | 횟수 | 획득포인트 | 누적포인트',
                            '---  | --- | --- | ---']
        for idx, item in enumerate(reporter_rank):
            point = 0
            """
            if item['count'] >= 10:
                point = 4
            elif item['count'] >= 6:
                point = 3
            elif item['count'] >= 3:
                point = 2
            else:
                point = 1
            """
            self.db.add_point(item['name'], point, start_date)
            self.db.update_point(item['name'])
            new_point = self.db.get_point(item['name'])
            if (new_point['earned'] - new_point['used']) > 0:
                reporter_table.append('@%s %s | %s | %s | %s' % (
                    item['name'],
                    medals[idx] if idx < len(medals) else '',
                    item['count'],
                    point,
                    new_point['earned'] - new_point['used']
                    )
                )

        spammer_rank = self.get_spammer_rank(records)
        spammer_table = ['계정 | 횟수', '---  | ---']
        for idx, item in enumerate(spammer_rank):
            spammer_table.append('<a href="http://steemit.com/@{name}">{name}</a> | {cnt}'
                        .format(name=item['name'], cnt=item['count'])
            )
       
        title = '🐶 %s 가이드독 스팸신고 활동 보고드립니다 (KR Guidedog\'s war on spam)' % period
        cont = ['<center>https://steemitimages.com/DQmQJySGPCWWhtS9Gw2aoR9pa3n43XCN5yvmKMwVWBk8Eym/Screen%20Shot%202017-10-11%20at%2023.25.25.png</center>',
                '# [공지] 가이드독 포인트는 더이상 발급되지 않습니다. 감사합니다.',
                '',
                '안녕하세요? @krguidedog입니다. %s의 KR가이드독 활동 내역을 보고드립니다.' % md,
                '',
                '%s에는 %s분께서 %s개의 스팸 글을 신고해 주셨습니다. %s명의 스패머들에게는 kr가이드독이 '
                '개발에 땀나도록 달려가서 kr 커뮤니티와 소통하는 방법에 대하여 친절하게 설명해 '
                '주었습니다.' % (
                    md, len(reporter_rank), len(records), len(spammer_rank) 
                ),
                '## 스팸글 신고 방법',
                'kr 태그나 kr- 로 시작하는 태그를 달고있는 글중에 스팸글을 발견하시면, 다음 명령어중 하나를 포함한 댓글을 달아주세요. 명령어만 넣어도 되고, 문장이랑 섞어서 넣어도 인식 됩니다. 외국인으로 판단되는 스패머를 대상으로 합니다.',
                '- kr-guide!',
                '- 전혀이해가안돼!',
                '- 무슨개소리야!',
                '',
                '스팸글 판단 기준:',
                '- 한글/영문 상관없이 명백히 표절인 글',
                '- 이해가 불가능할 정도의 엉터리 한글로 적힌 글.',
                '- 제대로 된 한글로 작성 되었으나, 누가봐도 인터넷에서 퍼온 글.',
                '- 한글 외의 언어로 작성 되었으나, 한국과 전혀 관계가 없는 글.',
                '',
                '해당 댓글이 달린 글에는 가이드독이 달려가서 친절한 소통을 시도합니다. 외국인글에 kr-guide!라고 적기 민망하신분은 한글 명령어인 "전혀이해가안돼!"를 사용하시길 바랍니다. ^^',
                '',
                '## 저작권 논란 글 신고 방법',
                '한국인이 포스팅한 글 중에서 불펌으로 의심될만한 글인 경우 아래 명령어로 저작권에 대한 안내를 해주세요.',
                '- @저작권신고',
                '',
                '## 신고해주신 분들에게 드리는 혜택',
                '가이드독 포인트는 더이상 발급되지 않습니다. 기존에 가지고 계신 포인트는 계속 사용하실 수 있습니다.'
                '',
                '## 가이드독 포인트 사용법',
                '### 칭찬해',
                '- 글에 @칭찬해가 포함된 댓글을 달면, 가이드독이 와서 칭찬댓글과 0.4 SBD 을 선물합니다.',
                '- 1 포인트 사용됩니다.',
                '### 축하해',
                '- 글에 @축하해가 포함된 댓글을 달면, 가이드독이 와서 축하댓글과 0.4 SBD 을 선물합니다.',
                '- 1 포인트 사용됩니다.',
                '### 감사해',
                '- 글에 @감사해가 포함된 댓글을 달면, 가이드독이 와서 감사댓글과 0.4 SBD 을 선물합니다.',
                '- 1 포인트 사용됩니다.',
                '### 위로해',
                '- 글에 @위로해가 포함된 댓글을 달면, 가이드독이 와서 감사댓글과 0.4 SBD 을 선물합니다.',
                '- 1 포인트 사용됩니다.',
                '### 홍보해',
                '- 글에 @홍보해가 포함된 댓글을 달면, 가이드독이 와서 보팅과 함께 리스팀을 해 줍니다. 한 글에는 한번만 동작합니다. 리스팀이 되는것을 감안하여 정말 좋은 글에만 사용 해 주세요.',
                '- 1 포인트 사용됩니다.',
                '',
                '### 특별히 구성된 가이드독 드림팀입니다',
                '<table><tr><td>http://i.imgur.com/7KVQf6i.jpg</td><td>http://i.imgur.com/pIqqVbm.png</td><td>http://i.imgur.com/Ft0qXcQ.png</td><td>http://i.imgur.com/oACf3Af.png</td><td>http://i.imgur.com/U6KILpr.png</td></tr><tr><td>개대리</td><td>개수습</td><td>개과장</td><td>개부장</td><td>개사원</td></tr></table>',
                '<table><tr><td>https://i.imgur.com/cGjDwLm.jpg</td><td>https://i.imgur.com/7zJDCee.jpg</td><td>https://i.imgur.com/G1VozdT.jpg</td><td>https://i.imgur.com/IhQNvMb.jpg</td><td>https://i.imgur.com/JZaU4tB.jpg</td></tr><tr><td>깜지</td><td>여름이</td><td>하니</td><td>써니</td><td>아리</td></tr></table>',
                '<table><tr><td>https://i.imgur.com/Di1kBXp.png</td><td>https://i.imgur.com/zla5JVW.jpg</td><td>https://i.imgur.com/tJJnC3W.jpg </td><td>https://i.imgur.com/7gzQiQ8.jpg</td><td></td></tr><tr><td>킹</td><td>별이</td><td>겨울이</td><td>모찌</td><td>----------------</td></tr></table>',
                '',
                '## 오늘의 히어로즈',
                '스팸글 신고는 귀찮고 시간도 잡아먹는 일입니다. 공익을 위한 이분들의 노력에'
                ' 박수를 보냅니다. 감사의 표시로 작은 보상을 준비 하였습니다.',
                '\n'.join(reporter_table),
                '',
                '---',
                '## 오늘의 스패머',
                '아래는 스패머들의 목록입니다. 혹시 억울하게 신고당한 분이 있다면 꼭 저에게 알려주세요!',
                '\n'.join(spammer_table),
                '- 반복이 3회 이상인 스패머의 글은 봇이거나 악의적 스패머일 수 있습니다.',
                '',
                '---',
                '### 현재 사용 가능 포인트',
                '\n'.join(self.get_all_points()),
                '---',
                '',
                '오늘도 kr 커뮤니티를 위해 노력해주신 분들께 깊은 감사를 드립니다.',
                '이 글에 **보팅**해 주시면 가이드독의 활동에 **큰힘**이 됩니다!',
                '---',
                'Created and operated by @asbear'
        ]
        return {'reporter': reporter_table,
                'spammer': spammer_table,
                'title': title,
                'body': '\n'.join(cont)}
