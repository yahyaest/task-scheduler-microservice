from django.urls import path
from rest_framework_nested import routers
from .views import TaskViewSet

router = routers.DefaultRouter()

router.register('tasks', TaskViewSet, basename='tasks')

urlpatterns = router.urls