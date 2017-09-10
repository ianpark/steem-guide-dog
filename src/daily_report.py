import sys
import json
from db import DataStore
from publisher import Publisher

def print_report(date):
    pb = Publisher({
        "reward": {
            "medals" : [
                "http://i.imgur.com/hv0zL8U.png",
                "http://i.imgur.com/xe9CD0S.png",
                "http://i.imgur.com/50zpz2p.png"],
            "pool": 10
        }
    })
    report = pb.generate_report(date)
    if report:
        print(report['body'])
    else:
        print('No data')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ('Usage: daily_report.py "2 Sep 2017"')
        sys.exit()
    print('Get daily report of %s' % sys.argv[1])
    print_report(sys.argv[1])