import json
import os
from performer import Performer
from db import DataStore

def on_complete(result):
    print(result)

CONFIG_FILE_PATH = 'etc/config.json'

with open(CONFIG_FILE_PATH) as config:   
    config = json.load(config)
db = DataStore(config)
keypath = os.path.expanduser(config['keyfile_path'])
pp = None
with open(keypath) as keyfile:    
    keyfile_json = json.load(keyfile)
    poster = config['posters'][0]
    pp = Performer(config,
                    poster,
                    keyfile_json[poster['account']],
                    on_complete)

def get_post():
    post = {
        'author': 'krguidedog',
        'identifier':'identifier',
        'bot_signal':'signal',
        'parent_author':'asbear',
        'parent_post_id': '@asbear/2tkz1b',
        'reported_count': 'reported_count',
        'root_title': 'root_title',
        'body': 'body'
    }
    return post

def get():
    return pp


def leave_praise(post=None):
    if not post:
        post = get_post()

print(db.get_point('krguidedog'))
print(db.get_usable_point('krguidedog'))