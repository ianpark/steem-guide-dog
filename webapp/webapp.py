import logging
from flask import Flask, render_template

log = logging.getLogger(__name__)
app = Flask(__name__)

config = None
db = None

def get_statistics():
    pass

@app.route("/")
def main_page():
    data = db.read_all()
    reporters = {}
    spammers = {}
    for i in data:
        if i['reporter'] in reporters:
            reporters[i['reporter']] += 1
        else:
            reporters[i['reporter']] = 1

        if i['author'] in spammers:
            spammers[i['author']] += 1
        else:
            spammers[i['author']] = 1
    log.info(reporters)
    log.info(spammers)
    
    return render_template('index.html', data = {'reporters': reporters, 'spammers': spammers} )    

def run_webapp(_config, _db):
    log.info('Start WebApp')
    global config, db
    config = _config
    db = _db
    app.run(host='0.0.0.0', debug = False)