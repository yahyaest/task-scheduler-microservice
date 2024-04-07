#!/bin/sh


PROTOCOL=${PROTOCOL:-http}
SOCKET=${SOCKET:-0.0.0.0:5000}
CHDIR=/code
WSGIFILE=/code/task_scheduler_app/wsgi.py
PROCESSES=${PROCESSES:-4}
THREADS=${THREADS:-2}
BUFFERSIZE=524288
STATS=${STATS:-0.0.0.0:9191}
CALLABLE=${CALLABLE:-application}
ENV=DEV

gateway_ip=$(getent hosts gateway | awk '{ print $1 }')

export GATEWAY_BASE_URL=http://$gateway_ip:3000
export JWT_SECRET='super-secret'

yes | python manage.py makemigrations > /dev/stderr
yes | python manage.py makemigrations api > /dev/stderr
yes yes | python manage.py migrate > /dev/stderr

rm -rf celerybeat.pid ./celery-worker-worker1.pid ./celery-worker-worker2.pid ./celery-worker-worker3.pid ./celery-worker-worker4.pid

# run the workers in background
nohup celery -A task_scheduler_app worker --pool=gevent --concurrency=8 -l debug  --autoscale=5,3 --without-gossip -E -n worker1@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &
nohup celery -A task_scheduler_app worker --pool=gevent --concurrency=8 -l debug  --autoscale=5,3 --without-gossip -E -n worker2@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &
nohup celery -A task_scheduler_app worker --pool=gevent --concurrency=8 -l debug  --autoscale=5,3 --without-gossip -E -n worker3@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &
nohup celery -A task_scheduler_app worker --pool=gevent --concurrency=8 -l debug  --autoscale=5,3 --without-gossip -E -n worker4@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &

# run the scheduler in background
nohup celery -A task_scheduler_app beat -l debug --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile logs/beat.txt &


if [ "$ENV" = "PROD" ]
then
        yes yes | uwsgi  --protocol $PROTOCOL --master \
        --socket $SOCKET --chdir $CHDIR --wsgi-file $WSGIFILE --callable $CALLABLE  --processes $PROCESSES \
        --threads $THREADS --buffer-size $BUFFERSIZE --stats  $STATS  > /dev/stderr

else
        python manage.py runserver 0.0.0.0:5000 > /dev/stderr
fi
