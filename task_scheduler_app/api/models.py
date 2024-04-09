from django.db import models
from datetime import datetime

DEFAULT_VARCHAR_SIZE = 255
DEFAULT_JSON_SIZE = 256000
STATUS_CHOICES = sorted([(item, item) for item in ["PENDING", "IN_PROGRESS", "SUCCESS", "FAILED"]])

class Task(models.Model):
    name = models.CharField(max_length=DEFAULT_VARCHAR_SIZE, blank=True, null=True)
    description = models.CharField(max_length=2048, blank=True, null=True)
    task_type = models.CharField(max_length=100, blank=True, null=True)
    cron_expression = models.CharField(max_length=DEFAULT_VARCHAR_SIZE, blank=True, null=True)
    retry_number = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=DEFAULT_VARCHAR_SIZE, choices=STATUS_CHOICES, default="PENDING")
    periodic_task = models.IntegerField(blank=True, null=True)
    user = models.CharField(max_length=DEFAULT_VARCHAR_SIZE, blank=True, null=True)
    args = models.JSONField(max_length=DEFAULT_JSON_SIZE, blank=True, null=True)
    begin_date = models.DateTimeField(default=datetime.now, blank=True)
    end_date = models.DateTimeField(null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(blank=True, null=True)
