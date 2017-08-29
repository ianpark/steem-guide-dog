import json
import logging
import time
from flask import Flask, render_template, send_from_directory

log = logging.getLogger(__name__)
app = Flask(__name__, static_url_path='/static')

config = None
db = None

def dict_to_list(source):
    list_keys = [ k for k in source ]
    list_values = [ v for v in source.values() ]
    list_key_value = [ [k,v] for k, v in source.items() ]
    return list_key_value

def get_data():
    data = db.read_all()
    reporters = {}
    suspects = {}
    for i in data:
        if i['reporter'] in reporters:
            reporters[i['reporter']] += 1
        else:
            reporters[i['reporter']] = 1

        if i['author'] in suspects:
            suspects[i['author']] += 1
        else:
            suspects[i['author']] = 1

    return {'reporters': dict_to_list(reporters),
            'suspects': dict_to_list(suspects),
            'reports': data}

# For all static files 
@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)

# For main page
@app.route('/')
def main_page():
    return app.send_static_file('index.html')

# For status JSON
@app.route("/status")
def status():
    return json.dumps(get_data())

def run_webapp(_config, _db):
    log.info('Start WebApp')
    global config, db
    config = _config
    db = _db
    app.run(host='0.0.0.0', debug = False)