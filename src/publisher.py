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

    def generate_report(self, start_date, end_date, point_base=True):
        records = self.db.get_rank_period(start_date, end_date)
        start = util.get_kr_time_from_timestamp(records[0]['report_time'])
        end = util.get_kr_time_from_timestamp(records[-1]['report_time'])
        md = util.get_kr_time(records[0]['report_time']).strftime('%-m월 %-d일')
        period = start + (' - ' + end if start != end else '')
        pool = self.config['reward']['pool']
        medals = self.config['reward']['medals']

        reporter_rank = self.get_rank(records)
        if point_base:
            reporter_table = ['불러주신분 | 횟수 | 획득포인트',
                              '---  | --- | ---']
            for idx, item in enumerate(reporter_rank):
                point = 1
                if item['count'] >= 20:
                    point = 5
                if item['count'] >= 10:
                    point = 3
                elif item['count'] >= 5:
                    point = 2
                else:
                    point = 1
                reporter_table.append('@%s %s | %s | %s' % (
                    item['name'],
                    medals[idx] if idx < len(medals) else '',
                    item['count'],
                    point
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
                '안녕하세요? @krguidedog 입니다. %s의 KR가이드독 활동 내역을 보고드립니다.' % md,
                '',
                '%s에는 %s분께서 %s개의 스팸 글을 신고해 주셨습니다. %s명의 스패머들에게는 제가 '
                '개발에 땀나도록 달려가서 kr 커뮤니티와 소통하는 방법에 대하여 친절하게 설명해 '
                '주었습니다.' % (
                    md, len(reporter_rank), len(records), len(spammer_rank) 
                ),
                '',
                '## 오늘의 히어로즈',
                '스팸글 신고는 귀찮고 시간도 잡아먹는 일입니다. 공익을 위한 이분들의 노력에'
                ' 박수를 보냅니다. 감사의 표시로 작은 보상을 준비 하였습니다.',
                '\n'.join(reporter_table),
                '- 보상은 현재 보상 풀 최대치인 %s SBD 기준입니다.' % pool,
                '- 현재 자동 송금기능은 제공되지 않으므로 수동으로 보내드립니다.',
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