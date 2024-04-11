import json
import math
from django.db.models import Case, When
from django.db import models
from django.shortcuts import render, get_object_or_404, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django import forms
from django.core.paginator import Paginator
from django_celery_beat.models import PeriodicTask
from task_scheduler_app.api.models import Task
from task_scheduler_app.api.serializer import TaskSerializer
from task_scheduler_app.core.tasks import test_celery_task, io_intensive_task
from task_scheduler_app.tools.helpers import logger
from task_scheduler_app.core.forms import DeleteTaskForm, LoginForm, RegisterForm, TaskForm, UpdateTaskForm
from task_scheduler_app.clients.gateway import Gateway

def getUserToken(request):
    cookies_obj = {}
    cookies_str : str = request.headers.get('Cookie', None)
    if cookies_str :
        cookies_list = cookies_str.split(";")
        for cookie in cookies_list:
            key = cookie.split("=")[0].strip()
            try:
                import ast
                value = ast.literal_eval(cookie.split("=")[1].strip())
                value = json.loads(value)
            except :
                value = cookie.split("=")[1].strip()
            cookies_obj[f'{key}'] = value
        return cookies_obj
    return None

def home_page(request):
    return render(request=request, template_name='home.html')

def login_page(request):
    # If token in cookies redirect home
    cookies = getUserToken(request)
    if cookies and cookies.get('token', None):
        response = HttpResponseRedirect('/')
        return response
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            data = {"email":email,"password": password}
            gateway = Gateway()
            token,error = gateway.login(data)
            if token:
                logger.info(f"token is : {token}")
                current_user = gateway.get_current_user()
                current_user_image = gateway.get_current_user_image()
                if current_user_image:
                    current_user["avatarUrl"] = current_user_image['filename']
                logger.info(f"current_user is : {current_user}")

                response = HttpResponseRedirect('/')
                # response.set_cookie("token", token)
                # response.set_cookie("user", json.dumps(current_user))
                response.set_cookie("token", token, secure=True, httponly=True)
                response.set_cookie("user", json.dumps(current_user), secure=True, httponly=True)
                return response
            else:
                if error:
                    error_message = error["message"]
                return render(request, 'login.html', {'form': form, 'error_message': error_message if error_message else None})            
    else:
        form = LoginForm()
    return render(request=request, template_name='login.html',context={'form': form})

def register_page(request):
    # If token in cookies redirect home
    cookies = getUserToken(request)
    if cookies and cookies.get('token', None):
        response = HttpResponseRedirect('/')
        return response
    
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if 'image' in request.FILES:
            form.files['image'] = request.FILES['image']
        if form.is_valid():
            try:
                email = form.cleaned_data.get('email')
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                phone = form.cleaned_data.get('phone')
                image_file = request.FILES.get('image')
                data = {
                    "email":email, 
                    "username": username, 
                    "password": password,
                    "phone": phone,
                    }
                logger.info(f"image_file is : {image_file} with type : {type(image_file)}")

                logger.info(f"image_file dict is : {image_file.__dict__}  ")
                gateway = Gateway()
                token,error = gateway.register(data)
                if token:
                    logger.info(f"token is : {token}")
                    data,error2 = gateway.upload_image(image_file, email)
                    logger.info(f"user image data is : {data}")
                    current_user = gateway.get_current_user()
                    current_user_image = gateway.get_current_user_image()
                    if current_user_image:
                        current_user["avatarUrl"] = current_user_image['filename']
                    logger.info(f"current_user is : {current_user}")

                    response = HttpResponseRedirect('/')
                    # response.set_cookie("token", token)
                    # response.set_cookie("user", json.dumps(current_user))
                    response.set_cookie("token", token, secure=True, httponly=True)
                    response.set_cookie("user", json.dumps(current_user), secure=True, httponly=True)
                    return response
                else:
                    if error:
                        error_message = error["message"]
                    return render(request, 'register.html', {'form': form, 'error_message': error_message if error_message else None})
            except forms.ValidationError as e:
                error_message = str(e)
                return render(request, 'register.html', {'form': form, 'error_message': error_message})  
        else:
            error_message = form.errors.get('password')
            logger.error(f"Form not valid : {error_message}")   
            return render(request, 'register.html', {'form': form, 'error_message': error_message})

    else:
        form = RegisterForm()
    return render(request=request, template_name='register.html', context={'form': form})

def logout_view(request):
    response = HttpResponseRedirect('/')
    response.delete_cookie("token")
    response.delete_cookie("user")
    return response

def tasks_page(request):
    try:
        token = None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
            user = cookies.get('user', None)
        
        if token is None:
            return HttpResponseRedirect('/login')
        
        # tasks_list = Task.objects.all().order_by('-last_update')

        # Order by last_update and if last_update is None put it at the end . SQL is :
        # SELECT *
        # FROM task
        # ORDER BY 
        #     CASE 
        #         WHEN last_update IS NULL THEN 1
        #         ELSE 0
        #     END,
        #     last_update DESC;

        tasks_list = Task.objects.all().filter(user=user.get('email', None)).order_by(
            Case(
                When(last_update__isnull=True, then=1),
                default=0,
                output_field=models.IntegerField(),
            ),
            '-last_update'
        )
        tasks_count = tasks_list.count()

        for task in tasks_list:
            try:
                periodic_task = PeriodicTask.objects.get(id=task.periodic_task)
                task.periodic_task = periodic_task
            except Exception as e:
                logger.error(f"Task {task.id} doesn't have a periodic task")
                task.periodic_task = None
        page_size = 20
        pages =  math.ceil(len(tasks_list) / page_size)
        page_range = list(range(1, pages + 1))
        paginator = Paginator(tasks_list, page_size)

        page_number = request.GET.get('page') if request.GET.get('page') else 1
        logger.info(f"page_number is : {page_number}")
        tasks = paginator.get_page(page_number)

        create_task_form = TaskForm(request.POST)

        return render(
            request=request, 
            template_name='tasks.html',
            context={
                'tasks': tasks, 
                'tasks_count': tasks_count,
                'page_range': page_range, 
                'current_page': int(page_number),
                'form': create_task_form
                }
            )
    except Exception as e:
        logger.error(f"Error in tasks_page view : {e}")
        return HttpResponseRedirect('/')

def disable_or_enable_task(request):
    try:
        token = None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
        
        if token is None:
            return HttpResponseRedirect('/login')
        
        form = UpdateTaskForm(request.POST)
        if form.is_valid():
            form.enable_or_disable_task()
            return HttpResponseRedirect('/tasks')
    except Exception as e:
        logger.error(f"Error in disable_or_enable_task view : {e}")
        return HttpResponseRedirect('/tasks')

def restart_task(request):
    try:
        token = None
        user =  None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
            user=cookies.get('user', None)
        
        if token is None or user is None:
            return HttpResponseRedirect('/login')
        
        form = UpdateTaskForm(request.POST)
        if form.is_valid():
            task_to_restart = form.restart_task()

            serializer_data = {
                'name': task_to_restart.name,
                'description': task_to_restart.description,
                'task_type': task_to_restart.task_type,
                'cron_expression': task_to_restart.cron_expression,
                'retry_number': task_to_restart.retry_number,
                'enabled': True,
                'user': user.get('email', None),
                'args': task_to_restart.args
            }
            serializer = TaskSerializer(data=serializer_data)
            if serializer.is_valid():
                serializer.save()
            return HttpResponseRedirect('/tasks')
    except Exception as e:
        logger.error(f"Error in restart_task view : {e}")
        return HttpResponseRedirect('/tasks')
    
def delete_task(request):
    try:
        token = None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
        
        if token is None:
            return HttpResponseRedirect('/login')

        form = DeleteTaskForm(request.POST)
        if form.is_valid():
            logger.info(f"Deleting task : {form.cleaned_data['task_id']}")
            form.delete_task()
            return HttpResponseRedirect('/tasks')
    except Exception as e:
        logger.error(f"Error in delete_task view : {e}")
        return HttpResponseRedirect('/tasks')

@require_POST
def create_task(request):
    try:
        logger.info(f"Creating Task View")
        token = None
        user =  None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
            user = cookies.get('user', None)

        form = TaskForm(request.POST)
        if form.is_valid():
            if token and user:
                # Create Task
                user_email = user.get('email', None)

                serializer_data = request.POST.copy()
                serializer_data['enabled'] = True
                serializer_data['user'] = user_email

                serializer = TaskSerializer(data=serializer_data)
                if serializer.is_valid():
                    serializer.save()

                return HttpResponseRedirect('/tasks')
            else:
                logger.error(f"Token or user not found")
                return HttpResponseRedirect('/tasks')
        else:
            logger.error(f"Form not valid : {form.errors}")
            return HttpResponseRedirect('/tasks')
    except Exception as e:
        logger.error(f"Error in create_task view : {e}")
        return HttpResponseRedirect('/tasks')

@require_POST
def edit_task(request, task_id):
    try:
        logger.info(f"Edit Task with id {{task_id}} View ")
        token = None
        cookies = getUserToken(request)
        if cookies:
            token=cookies.get('token', None)
        
        if token is None:
            return HttpResponseRedirect('/login')

        task = get_object_or_404(Task, id=task_id)
        form = TaskForm(request.POST)
        if form.is_valid():
            if token:
                serializer_data = request.POST.copy()
                serializer_data['enabled'] = task.enabled
                logger.info(f"Serializer Edit data : {serializer_data}")
                serializer = TaskSerializer(task, data=serializer_data)  # Pass the task instance here
                if serializer.is_valid():
                    serializer.save()
                return HttpResponseRedirect('/tasks')
            else:
                logger.error(f"Token not found")
                return HttpResponseRedirect('/tasks')
        else:
            logger.error(f"Form not valid : {form.errors}")
            return HttpResponseRedirect('/tasks')
    except Exception as e:
        logger.error(f"Error in edit_task view : {e}")
        return HttpResponseRedirect('/tasks')