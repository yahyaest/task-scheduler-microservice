import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_scheduler_app.settings')

app = Celery('task_scheduler_app')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

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
    print(f'Request: {self.request!r}')