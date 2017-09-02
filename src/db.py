import json
import logging
from tinydb import TinyDB, Query
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
    log = logging.getLogger(__name__)
    def __init__(self, config):
        """ Init """
        self.db = TinyDB(config['db_path'])
    
    def __del__(self):
        self.db.close()
    
    def store_report(self, report):
        reports = self.db.table('reports')
        qry = Query()
        result = reports.contains(
                    (qry.author == report['author']) &
                    (qry.permlink == report['permlink']))
        if result:
            self.log.info('Already exists: %s' % result)
            return False
        reports.insert(report)
        return True

    def read_all(self):
        reports = self.db.table('reports')
        return reports.all()

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