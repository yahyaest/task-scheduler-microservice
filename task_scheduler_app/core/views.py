from django.shortcuts import render, HttpResponse
from task_scheduler_app.core.tasks import test_celery_task, io_intensive_task
from task_scheduler_app.tools.helpers import logger


def test_celery(request):
    logger.info("Core View : Executing Celery task...")
    io_intensive_task.delay()
    logger.info("Core View : Celery task has been executed!")
    return HttpResponse("Celery task has been executed!")