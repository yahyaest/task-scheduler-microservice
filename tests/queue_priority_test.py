# python manage.py shell
from task_scheduler_app.api.tasks import tp1,tp2,tp3,tp4


# tp1.delay()
# tp2.delay()
# tp3.delay()
# tp4.delay()

tp2.apply_async(queue="prioritized_queued_tasks", priority=7)
tp1.apply_async(queue="prioritized_queued_tasks", priority=10)
tp1.apply_async(queue="prioritized_queued_tasks", priority=10)
tp3.apply_async(queue="prioritized_queued_tasks", priority=4)
tp4.apply_async(queue="prioritized_queued_tasks", priority=2)




from celery import group

task_group = group(tp1.s(), tp2.s(), tp3.s(), tp4.s())
task_group.apply_async(queue="prioritized_queued_tasks", priority=10)
