import util
from datetime import datetime
from operator import itemgetter
from collections import Counter
from db import DataStore


class Publisher:
    def __init__(self, config):
        self.db = DataStore(config)
        self.config = config
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

    def generate_report(self, start_date, end_date=None, point_base=True):
        if not end_date:
            end_date = start_date
        records = self.db.get_rank_period(start_date, end_date)
        if not records:
            return None
        start = util.get_kr_time_from_timestamp(records[0]['report_time'])
        end = util.get_kr_time_from_timestamp(records[-1]['report_time'])
        md = util.get_kr_time(records[0]['report_time']).strftime('%-m월 %-d일')
        period = start + (' - ' + end if start != end else '')
        pool = self.config['reward']['pool']
        medals = self.config['reward']['medals']

        reporter_rank = self.get_rank(records)
        if point_base:
            reporter_table = ['불러주신분 | 횟수 | 획득포인트 | 누적포인트',
                              '---  | --- | --- | ---']
            for idx, item in enumerate(reporter_rank):
                point = 1
                if item['count'] >= 10:
                    point = 4
                if item['count'] >= 6:
                    point = 3
                elif item['count'] >= 3:
                    point = 2
                else:
                    point = 1
                self.db.add_point(item['name'], point, start_date)
                self.db.update_point(item['name'])
                new_point = self.db.get_point(item['name'])
                reporter_table.append('@%s %s | %s | %s | %s' % (
                    item['name'],
                    medals[idx] if idx < len(medals) else '',
                    item['count'],
                    point,
                    new_point['earned'] - new_point['used']
                    )
                )
                
        else:
            reporter_table = ['불러주신분 | 횟수 | 비율 | 보상',
                            '---  | ---   | ---   | ---',]
            for idx, item in enumerate(reporter_rank):
                reporter_table.append('@%s %s | %s | %s%% | %s SBD' % (
                    item['name'],
                    medals[idx] if idx < len(medals) else '',
                    item['count'],
                    round(item['stake'] * 100, 1),
                    round(pool * item['stake'], 2),
                    )
                )

        spammer_rank = self.get_spammer_rank(records)
        spammer_table = ['계정 | 횟수', '---  | ---']
        for idx, item in enumerate(spammer_rank):
            spammer_table.append('<a href="http://steemit.com/@{name}">{name}</a> | {cnt}'
                        .format(name=item['name'], cnt=item['count'])
            )

        title = '🐶 가이드독 스팸신고 활동 보고드립니다. (%s)' % period
        cont = ['<center>http://i.imgur.com/mxdnAGI.png</center>',
                '안녕하세요? @asbear입니다. %s의 KR가이드독 활동 내역을 보고드립니다.' % md,
                '',
                '%s에는 %s분께서 %s개의 스팸 글을 신고해 주셨습니다. %s명의 스패머들에게는 kr가이드독이 '
                '개발에 땀나도록 달려가서 kr 커뮤니티와 소통하는 방법에 대하여 친절하게 설명해 '
                '주었습니다.' % (
                    md, len(reporter_rank), len(records), len(spammer_rank) 
                ),
                '## 스팸글 신고 방법',
                'kr 태그나 kr- 로 시작하는 태그를 달고있는 글중에 스팸글을 발견하시면, 다음 명령어중 하나를 포함한 댓글을 달아주세요. 명령어만 넣어도 되고, 문장이랑 섞어서 넣어도 인식 됩니다.',
                '- kr-guide!',
                '- 전혀이해가안돼!',
                '',
                '스팸글 판단 기준:',
                '- 한글/영문 상관없이 명백히 표절인 글',
                '- 이해가 불가능할 정도의 엉터리 한글로 적힌 글.',
                '- 제대로 된 한글로 작성 되었으나, 누가봐도 인터넷에서 퍼온 글.',
                '- 한글 외의 언어로 작성 되었으나, 한국과 전혀 관계가 없는 글.',
                '',
                '해당 댓글이 달린 글에는 가이드독이 달려가서 친절한 소통을 시도합니다. 외국인글에 kr-guide!라고 적기 민망하신분은 한글 명령어인 "전혀이해가안돼!"를 사용하시길 바랍니다. ^^',
                '',
                '## 신고해주신 분들에게 드리는 혜택',
                '매일매일 신고량을 정상하여 가이드독 포인트를 드립니다.',
                '- 10회 이상 - 4 포인트',
                '- 6회 이상 - 3 포인트',
                '- 3회 이상 - 2 포인트',
                '- 1회 이상 - 1 포인트',
                '',
                '## 가이드독 포인트 사용법',
                '### 칭찬해',
                '- 글에 @칭찬해가 포함된 댓글을 달면, 가이드독이 와서 칭찬댓글과 0.5 SBD를 선물합니다.',
                '- 3 포인트 사용됩니다.',
                '',
                '## 오늘의 히어로즈',
                '스팸글 신고는 귀찮고 시간도 잡아먹는 일입니다. 공익을 위한 이분들의 노력에'
                ' 박수를 보냅니다. 감사의 표시로 작은 보상을 준비 하였습니다.',
                '\n'.join(reporter_table),
                '- 전체 누적 순위는 <a href="http://soboru.co.uk:5000">여기</a>에서'
                ' 확인해 주세요.'
                '',
                '---',
                '## 오늘의 스패머',
                '아래는 스패머들의 목록입니다. 혹시 억울하게 신고당한 분이 있다면 꼭 저에게 알려주세요!',
                '\n'.join(spammer_table),
                '- 반복이 3회 이상인 스패머의 글은 봇이거나 악의적 스패머일 수 있습니다.',
                '- 전체 누적 스패머 순위는 <a href="http://soboru.co.uk:5000">여기</a>에서'
                ' 확인해 주세요.',
                '',
                '---',
                '오늘도 kr 커뮤니티를 위해 노력해주신 분들께 깊은 감사를 드립니다.',
                '이 글에 **보팅**해 주시면 가이드독의 활동에 **큰힘**이 됩니다!',          
        ]
        return {'reporter': reporter_table,
                'spammer': spammer_table,
                'pool': pool,
                'body': '\n'.join(cont)}
