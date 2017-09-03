import sys
import json
from db import DataStore
from publisher import Publisher

def print_report():

    pb = Publisher({
        "reward": {
            "medals" : [
                "http://i.imgur.com/hv0zL8U.png",
                "http://i.imgur.com/xe9CD0S.png",
                "http://i.imgur.com/50zpz2p.png"],
            "pool": 10
        }
    })

    report = pb.generate_report('2 Sep 2017', '2 Sep 2017')
    print(report['body'])

    
    pass

if __name__ == '__main__':
    print_report()