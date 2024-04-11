import json
import uuid
from datetime import datetime
import importlib
import traceback
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, ClockedSchedule
from django_celery_beat.utils import make_aware
from django_celery_results.models import TaskResult
from rest_framework import serializers
from cron_descriptor import  ExpressionDescriptor
from task_scheduler_app.api.models import Task
from task_scheduler_app.tools.helpers import logger

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['periodic_task']

    def create_periodic_task(self, validated_data):
        # Create a periodic task
        task_type = validated_data.get('task_type', None)

        if validated_data.get('cron_expression', None):
            try:
                if not task_type:
                    logger.error("Invalid task type")
                    raise serializers.ValidationError(
                        f"An invalid task type was requested to execute: {task_type}")

                parsed_obj = ExpressionDescriptor(
                    validated_data['cron_expression'])
                parsed_obj.get_description()
                parsed = parsed_obj._expression_parts[1:-1]

                schedule, _ = CrontabSchedule.objects.get_or_create(
                    month_of_year=parsed[3],
                    day_of_month=parsed[2],
                    day_of_week=parsed[4],
                    hour=parsed[1],
                    minute=parsed[0]
                )
                task = PeriodicTask(crontab=schedule)

            except Exception as e:
                logger.error(f"Error creating periodic task: {e}")
                logger.error(traceback.format_exc())  
                raise e
        else:
            due_datetime = make_aware(datetime.now())
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=due_datetime)
            task = PeriodicTask(clocked=clocked)
            task.one_off = True
        
        return task


    def verify_task_exists(self, task_type):
        try:
            # Check if the task exists in the tasks module
            module = importlib.import_module('task_scheduler_app.api.tasks')
            if hasattr(module, task_type):
                return True
            
            # Check if the task exists in the settings TASKS environment variable
            env_tasks = settings.CELERY_WORKER_TASKS.split(",")
            for task in env_tasks:
                env_task = slugify(task).replace("-", "_")
                if env_task == task_type:
                    return True
                break
                
            return False
        except Exception as e:
            logger.error(f"Error : {e}")
            logger.error(traceback.format_exc())  
            return False


    def to_internal_value(self, data):
        # Override the to_internal_value method to log the validation errors
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            # Log the validation errors
            logger.error(f"Validation error during deserialization: {exc.detail}")
            raise exc


    def create(self, validated_data):
        try:
            task_type = validated_data.get('task_type', None)
            task_type_slug = slugify(task_type).replace("-", "_")
            logger.info(f"Creating Task {task_type_slug} with data : {validated_data}")
            enabled = validated_data.get('enabled', True)
            retry_number = validated_data.get('retry_number', 0)
            task_args = validated_data.get('args', None)
            logger.info(f"Task args : {task_args}")
            if task_args is None:
                task_args = {}
            task_args["retry_number"] = retry_number

            task_exists = self.verify_task_exists(task_type_slug)

            if not task_exists:
                logger.error(f"Task {task_type} does not exist")
                raise serializers.ValidationError(
                    f"An invalid task type was requested to execute: {task_type}")
            

            # Create PeriodicTask
            periodic_task = self.create_periodic_task(validated_data)


            periodic_task.task = f'task_scheduler_app.api.tasks.{task_type_slug}'

            random_name =  "original_name:%s, random:%s" % (
                validated_data['name'], str(uuid.uuid4()))
            
            periodic_task.name = random_name

            validated_data['begin_date'] = validated_data.get('begin_date', timezone.now())
            periodic_task.start_time = validated_data['begin_date']

            if validated_data.get('end_date', None):
                periodic_task.expires = validated_data['end_date']

            periodic_task.enabled = enabled

            if task_args:
                periodic_task.kwargs = json.dumps(task_args)

            periodic_task.save()

            validated_data['periodic_task'] = periodic_task.id

            # Create Task
            task_instance = Task.objects.create(**validated_data)

            # Update task_id in kwargs of PeriodicTask
            periodic_task_kwargs = json.loads(periodic_task.kwargs)
            periodic_task_kwargs["task_id"] = task_instance.id
            periodic_task_kwargs["random_name"] = random_name

            periodic_task.kwargs = json.dumps(periodic_task_kwargs)
            periodic_task.save()

            return task_instance

        except Exception as e:
            logger.error(f"TaskSerializer.create Error : {e}")
            logger.error(traceback.format_exc())  
            raise e


    def update(self, instance, validated_data):
        try:
            logger.info(f"Updating Task {instance.id} with data : {validated_data}")
            # Get the celery task (PeriodicTask)
            celery_task_id = instance.periodic_task
            task = PeriodicTask.objects.get(pk=celery_task_id)

            # Update enabled field on related celery task (PeriodicTask)
            enabled = validated_data.get('enabled', None)
            if enabled is not None:
                task.enabled = validated_data['enabled']
            
            # Update name field on related celery task (PeriodicTask)
            if validated_data.get('name', None):
                random_name = "original_name:%s, random:%s" % (validated_data['name'], str(uuid.uuid4()))
                task.name = random_name
                str_kwargs = task.kwargs
                json_kwargs = json.loads(str_kwargs)
                json_kwargs["random_name"] = random_name
                json_kwargs["name"] = validated_data['name']
                task.kwargs = json.dumps(json_kwargs)

            # Update args field on related celery task (PeriodicTask)
            if validated_data.get('args', None):
                str_kwargs = task.kwargs
                json_kwargs = json.loads(str_kwargs)
                # TODO : Update arg of args if exists or add new arg to args not to overwrite all args
                json_kwargs["args"] = validated_data['args']
                task.kwargs = json.dumps(json_kwargs)

            # Update start_time field on related celery task (PeriodicTask)
            if validated_data.get('begin_date', None):
                task.start_time = validated_data['begin_date']

            # Update expires field on related celery task (PeriodicTask)
            if validated_data.get('end_date', None):
                task.expires = validated_data['end_date']

            # Update crontab field on related celery task (PeriodicTask)
            if validated_data.get('cron_expression', None):
                parsed_obj = ExpressionDescriptor(validated_data['cron_expression'])
                parsed_obj.get_description()
                parsed = parsed_obj._expression_parts[1:-1]
            
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    month_of_year=parsed[3],
                    day_of_month=parsed[2],
                    day_of_week=parsed[4],
                    hour=parsed[1],
                    minute=parsed[0]
                )
                task.crontab = schedule
                task.clocked = None  # https://github.com/celery/django-celery-beat/issues/344

            # Update retry_number field on related celery task (PeriodicTask)
            if validated_data.get('retry_number', None) is not None:
                str_kwargs = task.kwargs
                json_kwargs = json.loads(str_kwargs)
                json_kwargs["retry_number"] = validated_data['retry_number']
                task.kwargs = json.dumps(json_kwargs)

            task.save()
            instance = super(TaskSerializer, self).update(instance, validated_data)
            return instance
        
        except Exception as e:
            logger.error(f"TaskSerializer.update Error : {e}")
            logger.error(traceback.format_exc())  
            raise e