import time, random, functools
from datetime import datetime
from django_celery_beat.models import PeriodicTask
from celery import shared_task
from celery.signals import task_retry
from task_scheduler_app.tools.helpers import logger
from task_scheduler_app.api.models import Task
from task_scheduler_app.celery import app


# This is a Celery task that will be executed by the Celery worker.
# This celery tasks file will be empty as it will be loaded by replacing it content from the task_scheduler_app/api/tasks.py file from the docker container volume like this:
# volumes:
#   - ./task_scheduler_app/api/tasks.py:/code/task_scheduler_app/api/tasks.py



def get_tasks_from_kwargs(kwargs):
    random_name = kwargs.get('random_name', None)
    if(random_name):
        # Look for the related periodic_task, based on the name
        # TODO: Optimize this query to inner join / fetch related
        periodic_task = PeriodicTask.objects.get(name=random_name)
        try:
            current_task = Task.objects.get(periodic_task=periodic_task.id)
        except Exception as exception:
            logger.warning(f"Task related to periodic task {periodic_task.id} doesn't exist")
            periodic_task.delete()
            raise Exception(f"Task related to periodic task {periodic_task.id} doesn't exist")
        return periodic_task, current_task
    else:
        return None, None

def task_autoretry(*args_task, **kwargs_task):
    def on_failure(exc, task_id, args, kwargs, einfo):
        logger.info(einfo)
        logger.info(exc)
        logger.info("This task '%s' finished with failure" % task_id)

        periodic_task, current_task = get_tasks_from_kwargs(kwargs)
        current_task.status = "FAILED"
        current_task.end_date = datetime.now()
        current_task.last_update = datetime.now()

        if periodic_task.one_off == True:
            logger.info(f"The periodic task {periodic_task.id} is one_off and executed once, we will disable it")
            current_task.enabled = False
            periodic_task.enabled = False
            periodic_task.save()
        current_task.save()

    def on_success(retval, task_id, args, kwargs):
        logger.info("This task '%s' finished with success" % task_id)

        periodic_task, current_task = get_tasks_from_kwargs(kwargs)
        current_task.status = "SUCCESS"
        current_task.end_date = datetime.now()
        current_task.last_update = datetime.now()

        if periodic_task.one_off == True:
            logger.info(f"The periodic task {periodic_task.id} is one_off and executed once, we will disable it")
            current_task.enabled = False
            periodic_task.enabled = False
            periodic_task.save()
        current_task.save()

    def real_decorator(func):
        @app.task(*args_task, **kwargs_task)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wrapper.on_success = on_success
            wrapper.on_failure = on_failure

            try:
                wrapper.max_retries = kwargs.get('retry_number', 0)
                kwargs['attempt'] = wrapper.request.retries

                logger.info(
                    "Attempt: {attempt} of {attempts}".format(
                        attempt=wrapper.request.retries, attempts=wrapper.max_retries
                    )
                )

                logger.info('Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(
                    wrapper.request))

                logger.info("This task is just started")

                # Workaround: If a lot of tasks are programmed in the same minute
                # sleep the system for a few millisecond
                # This will delay the processing a little bit
                # and make starting after MM.000
                # To avoid starting all tasks at the same time
                x = random.randint(0, 1)
                time.sleep(x)

                periodic_task, current_task = get_tasks_from_kwargs(kwargs)
                current_task.status = "IN_PROGRESS"

                retval = func(wrapper, *args, **kwargs)
                wrapper.on_success(retval, wrapper.request.id, args, kwargs)

            except Exception as exc:
                wrapper.retry(exc=exc, countdown=10)

        return wrapper
    return real_decorator


@task_autoretry(bind=True)
def hello_ko(self, *args, **kwargs):
    logger.info("Hello World --> Failure Sample")
    logger.info("The given arguments are:")
    logger.info(kwargs)

    # Try with a file that never exists
    with open("/code/never_exists_file", "r") as file:
        data = file.read()


@task_autoretry(bind=True)
def hello_ok(self, *args, **kwargs):
    logger.info('Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(
        self.request))
    logger.info("Hello World --> Success Sample")
    logger.info("The given arguments are:")
    logger.info(kwargs)
