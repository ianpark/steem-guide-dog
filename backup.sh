DATE=`date '+%Y-%m-%d_%H-%M-%S'`.tar.gz

echo $DATE
tar zcvf ./db_backup/$DATE db
git add ./db_backup/$DATE
git commit -m 'DB Backup'
git push
