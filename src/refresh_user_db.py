from db import DataStore

def refresh_user_db():
    db = DataStore({})
    reports = db.read_all()
    for report in reports:
        db.add_user(report['reporter'])
        db.add_spammer(report['author'])
    
    for user in db.get_all_user():
        db.update_point(user['user_id'])

if __name__ == '__main__':
    refresh_user_db()