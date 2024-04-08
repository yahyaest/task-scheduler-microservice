from cron_descriptor import  ExpressionDescriptor
from django_celery_beat.models import CrontabSchedule
from task_scheduler_app.tools.helpers import logger


# Run this script with the following command:
# python manage.py runscript cron_expression
# docker exec -it task_scheduler python manage.py runscript cron_expression
# This script will parse a cron expression and create a CrontabSchedule object
def run(*args):
    cron_expression = "5 0 * 8 *"

    parsed_obj = ExpressionDescriptor(cron_expression)
    logger.info(f"Parsed object: {parsed_obj}")

    parsed_obj.get_description()
    logger.info(f"Description: {parsed_obj.get_description()}")

    parsed = parsed_obj._expression_parts[1:-1]
    logger.info(f"Parsed: {parsed}")

    schedule, _ = CrontabSchedule.objects.get_or_create(
        month_of_year=parsed[3],
        day_of_month=parsed[2],
        day_of_week=parsed[4],
        hour=parsed[1],
        minute=parsed[0]
    )

    logger.info(f"Schedule: {schedule}")
    logger.info(f"_ : {_}")




