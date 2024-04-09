from django.urls import path
from task_scheduler_app.core.views import home_page, login_page, register_page, logout_view, tasks_page, create_task, disable_or_enable_task, restart_task, delete_task


urlpatterns = [
    path('', home_page, name='home'),
    path('login', login_page, name='login'),
    path('register', register_page, name='register'),
    path('logout', logout_view, name='logout'),
    path('tasks', tasks_page, name='tasks'),
    path('create_task', create_task, name='create_task'),
    path('disable_or_enable_task', disable_or_enable_task, name='disable_or_enable_task'),
    path('restart_task', restart_task, name='restart_task'),
    path('delete_task', delete_task, name='delete_task'),
]
