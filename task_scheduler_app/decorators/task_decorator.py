import time, random, functools
from datetime import datetime
from django_celery_beat.models import PeriodicTask
from django.conf import settings
from task_scheduler_app.tools.helpers import logger
from task_scheduler_app.api.models import Task
# from task_scheduler_app.celery import app


use_redis_broker = settings.CELERY_USE_REDIS if hasattr(settings, 'CELERY_USE_REDIS') else False
use_rabbitmq_broker = settings.CELERY_USE_RABBITMQ if hasattr(settings, 'CELERY_USE_RABBITMQ') else False

if  use_redis_broker:
    from task_scheduler_app.celery import app
if  use_rabbitmq_broker:
    from task_scheduler_app.celery import rabbitmq_app
    

def get_celery_app(broker_choice):
    if broker_choice == 'rabbitmq' and use_rabbitmq_broker:
        return rabbitmq_app
    elif broker_choice == 'redis' and use_redis_broker:
        return app
    elif use_rabbitmq_broker and not use_redis_broker:
        return rabbitmq_app
    else:
        return app


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
        selected_app = get_celery_app(kwargs_task.get('broker_choice', None))
        logger.info(f"Selected app : {selected_app} for task {func.__name__}")
        logger.info(f"Task args_task in real_decorator : {args_task}")
        logger.info(f"Task kwargs_task in real_decorator : {kwargs_task}")
        # @app.task(*args_task, **kwargs_task)
        @selected_app.task(*args_task, **kwargs_task)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Task args_task : {args_task}")
            logger.info(f"Task kwargs_task : {kwargs_task}")
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