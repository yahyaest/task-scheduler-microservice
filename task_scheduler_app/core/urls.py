from django.urls import path
from task_scheduler_app.core import views


urlpatterns = [
    path('', views.test_celery, name="test_celery"),
]
