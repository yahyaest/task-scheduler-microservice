import json
from datetime import datetime
from django import template
from task_scheduler_app import settings
from task_scheduler_app.tools.helpers import *

register = template.Library()

@register.filter()
def replace(value, args):
    old = args.split(",")[0]
    new = args.split(",")[1]
    return value.replace(old, new)

@register.filter()
def split(value, arg):
    return value.split(arg)

@register.filter()
def list_to_string(value):
    return ', '.join(value)

@register.filter()
def list_length(value):
    return len(value)

@register.filter()
def get_gateway_url(value):
    return settings.GATEWAY_BASE_URL

@register.filter()
def get_user_image(value):
    user = json.loads(value)
    return user.get('avatarUrl', 'https://cdn-icons-png.flaticon.com/512/666/666201.png')

@register.filter()
def is_user_image(value):
    try:
        logger.info(f"Getting user image: {value}")
        user = json.loads(value)
        if user.get('avatarUrl', None):
            return True 
        return False
    except Exception as e:
        logger.error(f"Error getting user image: {e}")
        return False

@register.filter()
def round_number(value, digit):
    return round(value, digit)

@register.filter()
def division(value, value2):
    return value/value2

@register.filter()
def format_relative_time(value):
    input_date = datetime.fromisoformat(value[:-1]) if isinstance(value, str) else value
    current_date = datetime.now()

    time_difference = current_date - input_date
    seconds_difference = int(time_difference.total_seconds())
    minutes_difference = seconds_difference // 60
    hours_difference = minutes_difference // 60
    days_difference = hours_difference // 24
    months_difference = days_difference // 30
    years_difference = months_difference // 12

    if years_difference > 0:
        return f"{years_difference} year{'s' if years_difference != 1 else ''} ago"
    elif months_difference > 0:
        return f"{months_difference} month{'s' if months_difference != 1 else ''} ago"
    elif days_difference > 0:
        return f"{days_difference} day{'s' if days_difference != 1 else ''} ago"
    elif hours_difference > 0:
        return f"{hours_difference} hour{'s' if hours_difference != 1 else ''} ago"
    elif minutes_difference > 0:
        return f"{minutes_difference} minute{'s' if minutes_difference != 1 else ''} ago"
    else:
        return f"{seconds_difference} second{'s' if seconds_difference != 1 else ''} ago"

@register.filter()
def get_current_user_email(value):
    try:
        logger.info(f"Getting user email: {value}")
        return json.loads(value).get('email')
    except Exception as e:
        logger.error(f"Error getting user email: {e}")
