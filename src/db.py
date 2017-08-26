import logging
from tinydb import TinyDB, Query

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
    

        