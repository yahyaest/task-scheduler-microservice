#!/bin/sh

# Wsgi server configuration
PROTOCOL=${PROTOCOL:-http}
SOCKET=${SOCKET:-0.0.0.0:5000}
CHDIR=/code
WSGIFILE=/code/task_scheduler_app/wsgi.py
PROCESSES=${PROCESSES:-4}
THREADS=${THREADS:-2}
BUFFERSIZE=524288
STATS=${STATS:-0.0.0.0:9191}
CALLABLE=${CALLABLE:-application}

# Celery workers configuration
CELERY_WORKER_PROJECT_NAME=${CELERY_WORKER_PROJECT_NAME:-task_scheduler_app}
CELERY_RABBITMQ_WORKER_PROJECT_NAME=${CELERY_RABBITMQ_WORKER_PROJECT_NAME:-task_scheduler_rabbitmq_app}
CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://redis:6379}
CELERY_WORKER_CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-8}
CELERY_WORKER_AUTOSCALE=${CELERY_WORKER_AUTOSCALE:-5,3}
CELERY_WORKERS_COUNT=${CELERY_WORKERS_COUNT:-2}
CELERY_RABBITMQ_WORKERS_COUNT=${CELERY_RABBITMQ_WORKERS_COUNT:-2}
CELERY_WORKERS_QUEUES=${CELERY_WORKERS_QUEUES:-big_tasks,repetitive_tasks}
CELERY_WORKER_LOG_LEVEL=${CELERY_WORKER_LOG_LEVEL:-debug}

# Celery Broker configuration
CELERY_DEFAULT_BROKER=${CELERY_DEFAULT_BROKER:-redis}
CELERY_USE_REDIS=${CELERY_USE_REDIS:-True}
CELERY_USE_RABBITMQ=${CELERY_USE_RABBITMQ:-False}


echo "CELERY_WORKER_PROJECT_NAME=$CELERY_WORKER_PROJECT_NAME"

echo "CELERY_USE_REDIS=$CELERY_USE_REDIS"
echo "CELERY_USE_RABBITMQ=$CELERY_USE_RABBITMQ"

# Set the environment
ENV=DEV

gateway_ip=$(getent hosts gateway | awk '{ print $1 }')

export GATEWAY_BASE_URL=http://$gateway_ip:3000
export JWT_SECRET='super-secret'

yes | python manage.py makemigrations > /dev/stderr
yes | python manage.py makemigrations api > /dev/stderr
yes yes | python manage.py migrate > /dev/stderr

# remove the pid celery workers files
for i in $(seq 1 $CELERY_WORKERS_COUNT)
do
        rm -rf ./celery-worker-worker$i.pid
        rm -rf ./celery-worker-rabbitmq-worker_rabbitmq$i.pid
done
for queue in $(echo $CELERY_WORKERS_QUEUES | tr "," "\n")
do
        rm -rf ./celery-worker-$queue.pid
        rm -rf ./celery-worker-rabbitmq-$queue.pid
done

# run the workers in background
# for i in $(seq 1 $CELERY_WORKERS_COUNT)
# do
#         nohup celery -A $CELERY_WORKER_PROJECT_NAME worker --pool=gevent --concurrency=$CELERY_WORKER_CONCURRENCY -l $CELERY_WORKER_LOG_LEVEL  --autoscale=$CELERY_WORKER_AUTOSCALE --without-gossip -Q celery -E -n worker$i@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &
# done

if [ "$CELERY_USE_REDIS" = "True" ]
then
        echo "Starting Redis workers"
        export CELERY_BROKER_URL="redis://redis:6379"
        for i in $(seq 1 $CELERY_WORKERS_COUNT)
        do
                nohup celery -A $CELERY_WORKER_PROJECT_NAME worker --pool=prefork --concurrency=$CELERY_WORKER_CONCURRENCY -l $CELERY_WORKER_LOG_LEVEL  --autoscale=$CELERY_WORKER_AUTOSCALE --without-gossip -Q celery -E -n worker$i@%h --pidfile ./celery-worker-%n.pid --logfile logs/worker-%n.txt &
        done
        # run the queued workers in background
        for queue in $(echo $CELERY_WORKERS_QUEUES | tr "," "\n")
        do
                nohup celery -A $CELERY_WORKER_PROJECT_NAME worker --pool=prefork --concurrency=$CELERY_WORKER_CONCURRENCY -l $CELERY_WORKER_LOG_LEVEL  --autoscale=$CELERY_WORKER_AUTOSCALE --without-gossip -Q $queue -E -n worker_$queue@%h --pidfile ./celery-worker-$queue.pid --logfile logs/worker-$queue.txt &
        done

        # run the scheduler in background
        nohup celery -A $CELERY_WORKER_PROJECT_NAME beat -l $CELERY_WORKER_LOG_LEVEL --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile logs/beat.txt &
fi

if [ "$CELERY_USE_RABBITMQ" = "True" ]
then
        echo "Starting RabbitMQ workers"
        echo "CELERY_BROKER_URL Before=$CELERY_BROKER_URL"
        export CELERY_BROKER_URL="amqp://admin:admin@rabbitmq:5672"
        echo "CELERY_BROKER_URL After=$CELERY_BROKER_URL"
        for i in $(seq 1 $CELERY_RABBITMQ_WORKERS_COUNT)
        do
                nohup celery -A $CELERY_RABBITMQ_WORKER_PROJECT_NAME worker --pool=prefork --concurrency=$CELERY_WORKER_CONCURRENCY -l $CELERY_WORKER_LOG_LEVEL  --autoscale=$CELERY_WORKER_AUTOSCALE --without-gossip -Q rabbitmq_celery -E -n worker_rabbitmq$i@%h --pidfile ./celery-worker-rabbitmq-%n.pid --logfile logs/worker-rabbitmq-%n.txt &
        done
        # run the queued workers in background
        for queue in $(echo $CELERY_WORKERS_QUEUES | tr "," "\n")
        do
                nohup celery -A $CELERY_RABBITMQ_WORKER_PROJECT_NAME worker --pool=prefork --concurrency=$CELERY_WORKER_CONCURRENCY -l $CELERY_WORKER_LOG_LEVEL  --autoscale=$CELERY_WORKER_AUTOSCALE --without-gossip -Q $queue -E -n worker_rabbitmq_$queue@%h --pidfile ./celery-worker-rabbitmq-$queue.pid --logfile logs/worker-rabbitmq-$queue.txt &
        done

        # run the scheduler in background
        nohup celery -A $CELERY_RABBITMQ_WORKER_PROJECT_NAME beat -l $CELERY_WORKER_LOG_LEVEL --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile logs/beat_rabbitmq.txt &
fi

if [ "$ENV" = "PROD" ]
then
        yes yes | uwsgi  --protocol $PROTOCOL --master \
        --socket $SOCKET --chdir $CHDIR --wsgi-file $WSGIFILE --callable $CALLABLE  --processes $PROCESSES \
        --threads $THREADS --buffer-size $BUFFERSIZE --stats  $STATS  > /dev/stderr

else
        python manage.py runserver 0.0.0.0:5000 > /dev/stderr
fi
