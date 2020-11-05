nohup python -u run.py >> py_log.log 2>&1 &
nohup python -u crontab_for_cash.py >> cash_log.log 2>&1 &
nohup python -u crontab_for_rank.py >> rank_log.log 2>&1 &
nohup python -u run.py --logfile sync_worker1.log --without-web 2>&1 &
sqlacodegen mysql://root:!Syy950507@cdb-nfyowpkz.gz.tencentcdb.com:10166/bzly --outfile bzly.py