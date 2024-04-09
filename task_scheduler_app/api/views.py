from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django_celery_beat.models import PeriodicTask
from task_scheduler_app.api.models import Task
from task_scheduler_app.api.serializer import TaskSerializer
from task_scheduler_app.tools.helpers import logger

class TaskViewSet(ModelViewSet):
    """
    A simple ViewSet for viewing and editing Tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]


    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            task_id = instance.id
            periodic_task_id = instance.periodic_task
            logger.info(f"Deleting Task with id : {task_id} and it related PeriodicTask with id : {periodic_task_id}")
            Task.objects.filter(pk=task_id).delete()
            PeriodicTask.objects.filter(pk=periodic_task_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in TaskViewSet.destroy : {e}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)