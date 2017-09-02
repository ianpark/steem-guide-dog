import sys
import unittest
import json

# Local modules
sys.path.insert(0, '../src')
from db import DataStore


class TestDb(unittest.TestCase):

    def test_get_daily(self):
        db = DataStore({'db_path': './input_data/db.json'})
        print(db.get_report_count('asbear'))
        print(json.dumps(db.get_rank_period('31 Aug 2017', '31 Aug 2017')))
        pass

if __name__ == '__main__':
    unittest.main()