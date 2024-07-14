import time
import random
import glob
from django_celery_results.models import TaskResult
from django_celery_beat.models import PeriodicTask
from task_scheduler_app.tools.helpers import logger
from task_scheduler_app.decorators.task_decorator import task_autoretry
from task_scheduler_app.api.models import Task
# from task_scheduler_app.celery import app
from celery import shared_task


# This is a Celery task that will be executed by the Celery worker.
# This celery tasks file will be empty as it will be loaded by replacing it content from the task_scheduler_app/api/tasks.py file from the docker container volume like this:
# volumes:
#   - ./task_scheduler_app/api/tasks.py:/code/task_scheduler_app/api/tasks.py



def Fibonacci(n):
    # Check if input is 0 then it will
    # print incorrect input
    if n < 0:
        logger.error("Incorrect input")

    # Check if n is 0
    # then it will return 0
    elif n == 0:
        return 0

    # Check if n is 1,2
    # it will return 1
    elif n == 1 or n == 2:
        return 1

    else:
        return Fibonacci(n-1) + Fibonacci(n-2)


@task_autoretry(bind=True)
def hello_ko(self, *args, **kwargs):
    logger.info("Hello World --> Failure Sample")
    logger.info("The given arguments are:")
    logger.info(kwargs)

    # Try with a file that never exists
    with open("/code/never_exists_file", "r") as file:
        data = file.read()


@task_autoretry(bind=True, priority=10)
def hello_ok(self, *args, **kwargs):
    logger.info('Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(
        self.request))
    logger.info("Hello World --> Success Sample")
    logger.info("The given arguments are:")
    logger.info(kwargs)


@task_autoretry(bind=True)
def purge_task_results(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Purging successfull task results")
        TaskResult.objects.filter(status="SUCCESS").delete()
    except Exception as e:
        logger.error(f"Error purging task results: {e}")
        raise e

@task_autoretry(bind=True, queue='queued_tasks')
def tasks_stats(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Getting tasks stats")
        successfull_tasks_count = Task.objects.filter(status="SUCCESS").count()
        pending_tasks_count = Task.objects.filter(status="PENDING").count()
        in_progress_tasks_count = Task.objects.filter(status="IN_PROGRESS").count()
        failed_tasks_count = Task.objects.filter(status="FAILED").count()

        logger.info(f"Successfull tasks count: {successfull_tasks_count}")
        logger.info(f"Pending tasks count: {pending_tasks_count + in_progress_tasks_count}")
        logger.info(f"Failed tasks count: {failed_tasks_count}")

    except Exception as e:
        logger.error(f"Error getting tasks stats: {e}")
        raise e

@task_autoretry(bind=True)
def purge_celrery_workers_logs(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Purging Celery workers logs")
        
        # Get a list of all the .txt and .log files
        files = glob.glob('/code/logs/*.txt') + glob.glob('/code/logs/*.log')

        for file_name in files:
            logger.info(f"Purging file: {file_name}")
            with open(file_name, 'w') as file:
                file.write("")
    except Exception as e:
        logger.error(f"Error purging Celery workers logs: {e}")
        raise e

@task_autoretry(bind=True, queue='queued_tasks')
def periodic_tasks_stats(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Getting currently running periodic tasks stats")
        enabled_periodic_tasks = PeriodicTask.objects.filter(enabled=True, one_off=False)
        logger.info(f"Enabled running periodic tasks count: {enabled_periodic_tasks.count()}")
        for periodic_task in enabled_periodic_tasks:
            logger.info(f"Periodic task: {periodic_task.task} executed {periodic_task.total_run_count} times")

    except Exception as e:
        logger.error(f"Error getting periodic tasks stats: {e}")
        raise e

@task_autoretry(bind=True, queue='prioritized_queued_tasks', priority=2)
def low_priority_task(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Executing a low priority task")
        import time
        time.sleep(3)
        logger.info("Low priority task executed successfully")
    except Exception as e:
        logger.error(f"Error executing low priority task: {e}")
        raise e

@task_autoretry(bind=True, queue='prioritized_queued_tasks', priority=5)
def medium_priority_task(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Executing a medium priority task")
        import time
        time.sleep(3)
        logger.info("Medium priority task executed successfully")
    except Exception as e:
        logger.error(f"Error executing medium priority task: {e}")
        raise e

@task_autoretry(bind=True, queue='prioritized_queued_tasks', priority=10)
def high_priority_task(self, *args, **kwargs):
    try:
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        logger.info("Executing a high priority task")
        import time
        time.sleep(3)
        logger.info("High priority task executed successfully")
    except Exception as e:
        logger.error(f"Error executing high priority task: {e}")
        raise e
    
@task_autoretry(bind=True, broker_choice='rabbitmq')
def fibonacci_random_task(self, *args, **kwargs):
    try:
        logger.info(f"Executing task fibonacci_random_task, args: {args} kwargs: {kwargs}")
        logger.info(f"Executing task id {self.request.id}, args: {self.request.args!r} kwargs: {self.request.kwargs!r}")
        random_number = random.randint(40, 45)
        logger.info(f"Executing a Fibonacci task for n={random_number}")
        start_time = time.time()
        result = Fibonacci(random_number)
        end_time = time.time()
        logger.info(f"Fibonacci result for n={random_number} is {result} excuted in {end_time - start_time} seconds")
    except Exception as e:
        logger.error(f"Error executing Fibonacci task: {e}")
        raise e
    
@shared_task
def tp1():
    logger.info(f"Executing task tp1 with priority 10")
    time.sleep(3)
    logger.info(f"Task tp1 executed successfully")
    return

@shared_task
def tp2():
    logger.info(f"Executing task tp2 with priority 7")
    time.sleep(3)
    logger.info(f"Task tp2 executed successfully")
    return

@shared_task
def tp3():
    logger.info(f"Executing task tp3 with priority 4")
    time.sleep(3)
    logger.info(f"Task tp3 executed successfully")
    return

@shared_task
def tp4():
    logger.info(f"Executing task tp4 with priority 2")
    time.sleep(3)
    logger.info(f"Task tp4 executed successfully")
    return
