from django.contrib import admin
from .models import Task

# admin.site.register(Task)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'task_type', 'user', 'status', 'cron_expression', 'creation_date', 'last_update', 'periodic_task', 'enabled')
    list_filter = ('status', 'creation_date', 'last_update')
    list_editable = ('user',)
    search_fields = ('name', 'status')
    ordering = ('-creation_date', '-last_update')
    list_per_page = 10
