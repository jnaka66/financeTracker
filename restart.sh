#/bin/sh

pkill gunicorn
echo $?
docker start mongo4
gunicorn -w 4 --bind 0.0.0.0:6969 'notsite:app' --log-file FILE >out.txt
