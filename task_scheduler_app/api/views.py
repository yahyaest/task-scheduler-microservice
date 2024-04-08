from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from task_scheduler_app.api.models import Task
from task_scheduler_app.api.serializer import TaskSerializer

class TaskViewSet(ModelViewSet):
    """
    A simple ViewSet for viewing and editing Tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]

