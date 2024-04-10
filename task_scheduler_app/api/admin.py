from django.contrib import admin
from .models import Task

# admin.site.register(Task)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'status', 'creation_date', 'last_update', 'user')
    list_filter = ('status', 'creation_date', 'last_update')
    list_editable = ('user',)
    search_fields = ('name', 'status')
    ordering = ('-creation_date', '-last_update')
    list_per_page = 10
