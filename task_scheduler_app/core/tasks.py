import random
import time
from django.conf import settings
from celery import shared_task
from task_scheduler_app.tools.helpers import logger
# from task_scheduler_app.celery import app

use_redis_broker = settings.CELERY_USE_REDIS if hasattr(settings, 'CELERY_USE_REDIS') else False
use_rabbitmq_broker = settings.CELERY_USE_RABBITMQ if hasattr(settings, 'CELERY_USE_RABBITMQ') else False

current_app = None
if  use_redis_broker:
    from task_scheduler_app.celery import app
    current_app = app
if  use_rabbitmq_broker:
    from task_scheduler_app.celery import rabbitmq_app
    if not use_redis_broker:
        current_app = rabbitmq_app

# Implement task retry

@shared_task
@current_app.task(priority=10)
# @app.apply_async(queue="your_queue_that_can_handle_priority", priority=10) 
# Priority isn't natively unsuported by Redis unlike RabbitMQ : 
# https://docs.celeryq.dev/en/latest/userguide/routing.html#redis-message-priorities
# https://docs.celeryq.dev/en/stable/history/whatsnew-3.0.html#redis-priority-support
def test_celery_task():
    logger.info("Core Task test_celery_task : Executing Celery task to print numbers from 0 to 4...")
    for i in range(5):
        logger.info(i)    
    logger.info("Core Task test_celery_task : Celery task to print numbers from 0 to 4 has been executed!")
    return "Done"

@shared_task
def random_success_task():
    logger.info("Core Task : Executing Celery task to test random success...")
    random_value = random.random()
    logger.info(f"Core Task random_success_task : Random value: {random_value}")
    if random_value < 0.6:  # 60% chance to fail
        logger.error("Core Task : Task failed.")
        raise Exception("Task failed.")
    else:
        logger.info("Core Task random_success_task : Task succeeded.")
        return "Task succeeded."
    
@shared_task
@current_app.task(queue='big_tasks')
def io_intensive_task():
    start_time = time.time()

    logger.info("Core Task io_intensive_task : Start Executing I/O intensive task...")

    # Empty the file before the loop
    with open('./testfile.txt', 'w') as f:
        pass

    for i in range(25000):
        with open('./testfile.txt', 'a') as f:
            f.write(f'Hello, world! - {i}\n')
        with open('./testfile.txt', 'r') as f:
            lines = f.readlines()

    end_time = time.time()
    execution_time = end_time - start_time

    logger.info(f"Core Task io_intensive_task : Task completed. Execution time: {execution_time} seconds.")
    return "Task completed."

@shared_task
@current_app.task(queue='repetitive_tasks')
def short_task():
    logger.info("Core Task short_task : Executing Celery task to test random success...")
    random_value = random.random()
    logger.info(f"Core Task short_task : Random value: {random_value}")
    logger.info("Core Task short_task : Task succeeded.")





