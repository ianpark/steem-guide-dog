import json
import logging
from tinydb import TinyDB, Query, where
from tinydb.operations import increment
from datetime import datetime
from pytz import timezone

KR = timezone('Asia/Seoul')

"""
Table: reports
    reporter    : string
    author      : string
    permlink    : string
    report_time : string
    bot_signal  : string
"""

class DataStore:
    """ 
    DB class using TinyDB
    TODO: Reimplement usign proper DB
    """
    db = TinyDB('db/db.json')
    db_point = TinyDB('db/point.json')
    db_user = TinyDB('db/user.json')
    log = logging.getLogger(__name__)
    def __init__(self, config):
        self.config = config
        pass

    def __del__(self):
        self.db.close()
        self.db_point.close()
    
    def store_report(self, post):
        tbl = self.db.table('reports')
        qry = Query()
        result = tbl.contains(
                    (qry.author == report['author']) &
                    (qry.permlink == report['permlink']))
        if result:
            self.log.info('Already exists: %s' % result)
            return False

        tbl.insert({
            'reporter': post['author'],
            'author': post['parent_author'],
            'permlink': post['parent_permlink'],
            'report_time': datetime.now(),
            'bot_signal': post['bot_signal']
        })
        self.add_user(report['reporter'])
        self.add_spammer(report['author'])

        return True
    
    def store_praise(self, post):
        tbl = self.db.table('praises')
        tbl.insert({
            'reporter': post['author'],
            'author': post['parent_author'],
            'permlink': post['parent_permlink'],
            'report_time': datetime.now(),
            'bot_signal': post['bot_signal'],
            'processed': False
        })
        return True   

    def add_user(self, user_id):
        user = self.db_user.table('user')
        qry = Query()
        result = user.get(qry.user_id == user_id)
        if not result:
            user.insert({'user_id': user_id, 'report_count': 1, 'spam_count': 0, 'point_earned' : 0, 'point_used': 0})
        else:
            user.update(increment('report_count'), eids=[result.eid])

    def add_spammer(self, user_id):
        user = self.db_user.table('user')
        qry = Query()
        result = user.get(qry.user_id == user_id)
        if not result:
            user.insert({'user_id': user_id, 'report_count': 0, 'spam_count': 1, 'point_earned' : 0, 'point_used': 0})
        else:
            user.update(increment('spam_count'), eids=[result.eid])

    def get_all_user(self):
        return self.db_user.table('user').all()

    def read_all(self, limit=None):
        reports = self.db.table('reports')
        if not limit:
            return reports.all()
        else:
            return reports.search(where('report_time') >= limit)

    def get_report_count(self, user_id):
        reports = self.db.table('reports')
        qry = Query()
        return reports.count(qry.reporter == user_id)

    def get_reported_count(self, user_id):
        reports = self.db.table('reports')
        qry = Query()
        return reports.count(qry.author == user_id)
    
    def get_rank_period(self, start_date, end_date):
        reports = self.db.table('reports')
        qry = Query()
        start = KR.localize(
            datetime.strptime(start_date, '%d %b %Y')
                .replace(hour=0, minute=0, second=0))

        end = KR.localize(
            datetime.strptime(end_date, '%d %b %Y')
                .replace(hour=23, minute=59, second=59))

        result = reports.search((qry.report_time >= start.timestamp()) &
                             (qry.report_time <= end.timestamp()))
        return result
    """
        Points
    """
    def update_point(self, user_id):
        point = self.get_point(user_id)
        user = self.db_user.table('user')
        qry = Query()
        result = user.get(qry.user_id == user_id)
        if result:
            user.update({
                'point_earned': point['earned'],
                'point_used': point['used']
                },
                eids=[result.eid])

    def add_point(self, user_id, amount, date):
        reports = self.db_point.table('earned')
        qry = Query()
        reports.remove((qry.date == date) & (qry.user_id == user_id))
        # a user can earn point only once a day
        reports.insert({
            'user_id': user_id, 
            'amount': amount, 
            'date': date
            })
        self.update_point(user_id)
    
    def use_point(self, user_id, amount):
        reports = self.db_point.table('used')
        reports.insert({
            'user_id': user_id, 
            'amount': amount, 
            'date': datetime.now().strftime('%d %b %Y')
            })
        self.update_point(user_id)

    def get_point(self, user_id):
        qry = Query()
        earned_point = 0
        used_point = 0
        for earned in self.db_point.table('earned').search(qry.user_id == user_id):
            earned_point += earned['amount']
        for used in self.db_point.table('used').search(qry.user_id == user_id):
            used_point += used['amount']
        return {'earned': earned_point, 'used': used_point}

    def get_usable_point(self, user_id):
        point = self.get_point(user_id)
        return (point['earned'] - point['used'])