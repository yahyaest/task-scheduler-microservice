from datetime import datetime
from django import forms
from django_celery_beat.models import PeriodicTask
from task_scheduler_app.api.models import Task
from task_scheduler_app.tools.helpers import logger


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "input input-bordered", "placeholder": "Email", "required": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "input input-bordered", "placeholder": "Password", "required": True}),
    )

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "input input-bordered", "placeholder": "Email", "required": True}),
    )
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Username", "required": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "input input-bordered", "placeholder": "Password", "required": True}),
    )
    password2 = forms.CharField(
        label="Password Confirmation",
        widget=forms.PasswordInput(attrs={"class": "input input-bordered", "placeholder": "Password", "required": True}),
    )
    phone = forms.IntegerField(
        label="Phone",
        widget=forms.NumberInput(attrs={"class": "input input-bordered", "placeholder": "Phone", "required": True}),
    )
    image = forms.ImageField(
        label="Account Photo",
        widget=forms.FileInput(attrs={"id": "image-input", "class": "file-input file-input-bordered file-input-success w-full max-w-xs", "placeholder": "Account Photo", "required": True}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password != password2:
            self.add_error('password', 'Passwords do not match.')

        return cleaned_data
    
    def clean_image(self):
        image = self.files.get('image')

        if image is not None:
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.add_error('image', 'Invalid file format. Please upload a valid image.')
            if image.size > 5 * 1024 * 1024:  # 5 MB
                self.add_error('image', 'File size exceeds the allowed limit (5 MB)')

        return image

class TaskForm(forms.Form):
    name = forms.CharField(
        label="Name",
        widget=forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Task Name"}),
    )
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Task Description"}),
    )
    task_type = forms.CharField(
        label="Task Type",
        widget=forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Task Type"}),
    )
    cron_expression = forms.CharField(
        label="Cron Expression",
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Cron Expression"}),
    )
    retry_number = forms.IntegerField(
        label="Retry Number",
        widget=forms.NumberInput(attrs={"class": "input input-bordered", "placeholder": "Retry Number"}),
    )
    # enabled = forms.BooleanField(
    #     label="Enabled",
    #     widget=forms.CheckboxInput(attrs={"class": "checkbox"}),
    # )

class UpdateTaskForm(forms.Form):
    task_id = forms.IntegerField()

    def enable_or_disable_task(self):
        try:
            task_id = self.cleaned_data['task_id']
            periodic_task_id = Task.objects.get(id=task_id).periodic_task
            task = Task.objects.get(id=task_id)
            logger.info(f"{'Enabling' if not task.enabled else 'Disabling'} task with id: {task_id} and its related PeriodicTask with id: {periodic_task_id}")
            task.enabled = not task.enabled
            task.save()
            periodic_task = PeriodicTask.objects.get(id=periodic_task_id)
            periodic_task.enabled = task.enabled
            periodic_task.save()
        except Task.DoesNotExist:
            logger.error(f"Task with id: {self.cleaned_data['task_id']} does not exist")
        except Exception as e:
            logger.error(f"Error in enable_or_disable_task: {e}")
    
    def restart_task(self):
        try:
            task_id = self.cleaned_data['task_id']
            task = Task.objects.get(id=task_id)
            return task
        except Task.DoesNotExist:
            logger.error(f"Task with id: {self.cleaned_data['task_id']} does not exist")
        except Exception as e:
            logger.error(f"Error in restart_task: {e}")


class DeleteTaskForm(forms.Form):
    task_id = forms.IntegerField()

    def delete_task(self):
        try:
            task_id = self.cleaned_data['task_id']
            periodic_task_id = Task.objects.get(id=task_id).periodic_task
            logger.info(f"Deleting task with id: {task_id} and its related PeriodicTask with id: {periodic_task_id}")
            Task.objects.filter(pk=task_id).delete()
            PeriodicTask.objects.filter(pk=periodic_task_id).delete()
        except Task.DoesNotExist:
            logger.error(f"Task with id: {self.cleaned_data['task_id']} does not exist")
        except Exception as e:
            logger.error(f"Error in delete_task: {e}")
