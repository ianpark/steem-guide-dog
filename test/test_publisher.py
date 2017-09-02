import sys
import json
import unittest

# Local modules
sys.path.insert(0, '../src')
from publisher import Publisher


class TestDb(unittest.TestCase):

    def test_get_daily(self):
        with open('./input_data/db_range.json') as sample:
            data = json.load(sample)
        pb = Publisher({
            "reward": {
                "medals" : [
                    "http://i.imgur.com/hv0zL8U.png",
                    "http://i.imgur.com/xe9CD0S.png",
                    "http://i.imgur.com/50zpz2p.png"],
                "pool": 10
            }
        })

        print(pb.get_rank(data))
        print('\n'.join(pb.generate_report(data)))
        
        pass

if __name__ == '__main__':
    unittest.main()