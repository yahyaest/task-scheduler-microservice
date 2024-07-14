import os

from celery import Celery
from django.conf import settings
from task_scheduler_app.tools.helpers import logger

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_scheduler_app.settings')

use_redis_broker = settings.CELERY_USE_REDIS if hasattr(settings, 'CELERY_USE_REDIS') else False
use_rabbitmq_broker = settings.CELERY_USE_RABBITMQ if hasattr(settings, 'CELERY_USE_RABBITMQ') else False


if use_redis_broker or use_rabbitmq_broker == False:
    logger.info("YMA ===> Using Redis as the broker for Celery.")
    app = Celery('task_scheduler_app')

    # Using a string here means the worker doesn't have to serialize
    # the configuration object to child processes.
    # - namespace='CELERY' means all celery-related configuration keys
    #   should have a `CELERY_` prefix.
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Load task modules from all registered Django apps.
    app.autodiscover_tasks()

    # Celery task priority configuration
    # from kombu import Exchange, Queue

    # app.conf.task_queues = [
    #     Queue('celery', Exchange('celery'), routing_key='celery',queue_arguments={'x-max-priority': 10}),
    #     Queue('queued_tasks', Exchange('queued_tasks'), routing_key='queued_tasks',queue_arguments={'x-max-priority': 10}),
    #     Queue('prioritized_queued_tasks', Exchange('prioritized_queued_tasks'), routing_key='prioritized_queued_tasks',queue_arguments={'x-max-priority': 10}),
    # ]
    app.conf.task_queue_max_priority = 10
    app.conf.task_default_priority = 5

    # Celery Beat Configuration
    app.conf.beat_schedule = {
        'backend_cleanup': {
            'task': 'celery.backend_cleanup',
            'schedule':120, # 2 minutes
        },
        # 'backend_test': {
        #     'task': 'task_scheduler_app.core.tasks.test_celery_task',
        #     'schedule': 60, # 1 minute
        # },
        # 'random_success_task': {
        #     'task': 'task_scheduler_app.core.tasks.random_success_task',
        #     'schedule': 30, # 30 seconds
        # },
        # 'io_intensive_task': {
        #     'task': 'task_scheduler_app.core.tasks.io_intensive_task',
        #     'schedule': 120, # 2 minutes
        # }, 
        # 'short_task': {
        #     'task': 'task_scheduler_app.core.tasks.short_task',
        #     'schedule': 5, # 5 seconds
        # }, 
    }

    @app.task(bind=True, ignore_result=True)
    def debug_task(self):
        logger.info(f'Request: {self.request!r}')

if use_rabbitmq_broker:
    rabbitmq_broker_url = settings.CELERY_RABBITMQ_BROKER_URL
    admin_broker_url = settings.CELERY_BROKER_URL
    logger.info(f"YMA ===> Using RabbitMQ as the broker for Celery.")
    rabbitmq_app = Celery(
        'task_scheduler_rabbitmq_app',
        broker=rabbitmq_broker_url,
        backend='django-db',
        )
    
    rabbitmq_app.config_from_object('django.conf:settings', namespace='CELERY')

    # Load task modules from all registered Django apps.
    rabbitmq_app.autodiscover_tasks()
    rabbitmq_app.conf.task_queue_max_priority = 10
    rabbitmq_app.conf.task_default_priority = 5
    # Celery Beat Configuration
    rabbitmq_app.conf.beat_schedule = {
        'backend_cleanup_rabbitmq': {
            'task': 'celery.backend_cleanup',
            'schedule':120, # 2 minutes
        },
}

    @rabbitmq_app.task(bind=True, ignore_result=True)
    def debug_task(self):
        logger.info(f'Request: {self.request!r}')