import json
import logging
import time
from datetime import datetime
from flask import Flask, render_template, send_from_directory

log = logging.getLogger(__name__)
app = Flask(__name__, static_url_path='/static')

config = None
db = None

def get_data():
    data = db.read_all(datetime.now().timestamp() - 60 * 60 * 72)
    user = [
        [x['user_id'],
        x['report_count'],
        x['spam_count'],
        x['point_earned'],
        x['point_used']] for x in db.get_all_user()
    ]
    return {'users': user,
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