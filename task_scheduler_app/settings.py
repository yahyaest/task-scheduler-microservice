"""
Django settings for task_scheduler_app project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import environ
import logging
from task_scheduler_app.tools.helpers import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ztf^&y&c76y50@e7u!1p9$yva6znu9(zfza!$ihf5cv=tea9sv'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

# Settings from environment
env = environ.Env(
    DATABASE_URL=(str, 'psql://postgres:postgres@postgres:5432/task-scheduler'),
    GATEWAY_BASE_URL=(str, None),
    CELERY_WORKER_TASKS=(str, None),
    CELERY_BROKER_URL=(str, 'redis://redis:6379'),
    CELERY_RESULT_BACKEND=(str, 'redis://redis:6379'),
    CELERY_RABBITMQ_BROKER_URL=(str, 'amqp://admin:admin@rabbitmq:5672'),
    CELERY_DEFAULT_BROKER=(str, 'redis'),
    CELERY_USE_REDIS=(bool, True),
    CELERY_USE_RABBITMQ=(bool, False),
)

DATABASE_URL = env('DATABASE_URL')
GATEWAY_BASE_URL = env('GATEWAY_BASE_URL')

# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_filters',
    'multiselectfield',
    'rest_framework',
    'template_partials',
    'task_scheduler_app.core',
    'task_scheduler_app.api'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'task_scheduler_app.api.middleware.auth_middleware.JWTAuthMiddleware',
]

ROOT_URLCONF = 'task_scheduler_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'task_scheduler_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL'),
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_ROOT = 'staticfiles/'
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES' : (
        # 'rest_framework.authentication.SessionAuthentication',
        'task_scheduler_app.api.auth.user.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# CELERY SETTINGS

# CELERY_BROKER_URL = 'redis://redis:6379'
# CELERY_RESULT_BACKEND = 'redis://redis:6379'
# CELERY_RESULT_BACKEND = 'django-db'
CELERY_WORKER_TASKS = env('CELERY_WORKER_TASKS')
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_RESULT_EXPIRES = '60'  # 1 minute
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CELERY BROKER SETTINGS
CELERY_DEFAULT_BROKER = env('CELERY_DEFAULT_BROKER')
CELERY_USE_REDIS = env('CELERY_USE_REDIS')
CELERY_USE_RABBITMQ = env('CELERY_USE_RABBITMQ')
CELERY_RABBITMQ_BROKER_URL = env('CELERY_RABBITMQ_BROKER_URL')

# CELERY EVENTS SETTINGS
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# # CELERY QUEUES AND ROUTINGS CONFIGURATION
# CELERY_QUEUES = {
#     'big_tasks': {'exchange': 'big_tasks', 'routing_key': 'big_tasks'},
#     'repetitive_tasks': {'exchange': 'repetitive_tasks', 'routing_key': 'repetitive_tasks'},
# }

# CELERY_ROUTES =  ([
#     ('task_scheduler_app.core.tasks.io_intensive_task', {'queue': 'big_tasks', 'exchange': 'big_tasks'}),
#     ('task_scheduler_app.core.tasks.short_task', {'queue': 'repetitive_tasks', 'exchange': 'repetitive_tasks'})
#     # ('feed.tasks.*', {'queue': 'feeds'}),
#     # ('web.tasks.*', {'queue': 'web'}),
#     # (re.compile(r'(video|image)\.tasks\..*'), {'queue': 'media'}),
# ],)

# CELERY PRIORITY CONFIGURATION
# BROKER_TRANSPORT_OPTIONS = {
#     'priority_steps': list(range(10)),
#     'sep': ':',
#     'queue_order_strategy': 'priority',
# }

# Add a timeout to all Celery tasks.
CELERY_TASK_TIME_LIMIT = 10 * 60

CELERYD_PREFETCH_MULTIPLIER = 0
# CELERY_ACKS_LATE = True
# CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_COMPRESSION = 'gzip'
CELERY_MESSAGE_COMPRESSION = 'gzip'

import datetime
import logging
import http.client

# Workaround httpclient logger

httpclient_logger = logging.getLogger("requests.packages.urllib3")


def httpclient_log(*args):
    httpclient_logger.log(logging.DEBUG, " ".join(args))

# mask the print() built-in in the http.client module to use
# logging instead
http.client.print = httpclient_log
# enable debugging
http.client.HTTPConnection.debuglevel = 1
logging.captureWarnings(True)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(name)s] %(levelname)s::(%(process)d %(threadName)s)::%(module)s:%(lineno)d - %(message)s - %(msecs)d'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter':'default'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.channels.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'Task-Scheduler': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'requests.packages.urllib3': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}


# Wait for postgres to be ready
count = 1
timer = 10
microservice_name= os.path.basename(os.path.dirname(__file__))
while True:
    from django.db import connections
    from django.db.utils import OperationalError
    import time

    old_settings = os.environ['DJANGO_SETTINGS_MODULE']
    os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % microservice_name
    conn = connections["default"]  # or some other key in `DATBASES`
    os.environ['DJANGO_SETTINGS_MODULE'] = old_settings
    try:
        logging.info("Try (%d) to connect to the database" % count)
        c = conn.cursor()
        logging.info("The database is ready, let's start...")
        break
    except Exception as e:
        logging.error(e)
        logging.warning("The database is not ready, let's try again in %s second(s)..." % timer)
        time.sleep(5)
    finally:
        count = count + 1 
