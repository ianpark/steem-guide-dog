import sys
from tinydb import TinyDB, Query, where

user_id = sys.argv[1]

print ("rescue %s" % user_id)

db = TinyDB('../db/db.json')
tbl = db.table('reports')
qry = Query()
result = tbl.remove((qry.author == user_id))
print(result)
