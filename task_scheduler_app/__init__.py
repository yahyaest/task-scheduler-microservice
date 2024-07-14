# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import os
from django.conf import settings
# from .celery import app as celery_app
# Ensure the settings module is set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_scheduler_app.settings')

use_redis_broker = settings.CELERY_USE_REDIS if hasattr(settings, 'CELERY_USE_REDIS') else False
use_rabbitmq_broker = settings.CELERY_USE_RABBITMQ if hasattr(settings, 'CELERY_USE_RABBITMQ') else False

if  use_redis_broker:
    from .celery import app as celery_app
if  use_rabbitmq_broker:
    from .celery import rabbitmq_app as celery_rabbitmq_app

if use_redis_broker and use_rabbitmq_broker:
    celery_apps = ('celery_app', 'celery_rabbitmq_app',)
elif use_redis_broker and not use_rabbitmq_broker:
    celery_apps = ('celery_app',)
elif not use_redis_broker and use_rabbitmq_broker:
    celery_apps = ('celery_rabbitmq_app',)
else:
    celery_apps = ('celery_app',)

__all__ = celery_apps