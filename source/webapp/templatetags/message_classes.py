from django import template
from django.contrib.messages import DEBUG, INFO, SUCCESS, WARNING, ERROR

register = template.Library()

DEFAULT_CLASSES = {
    DEBUG: 'alert-secondary',
    INFO: 'alert-primary',
    SUCCESS: 'alert-success',
    WARNING: 'alert-warning',
    ERROR: 'alert-danger'
}


@register.filter
def get_class_filter(message):
    return DEFAULT_CLASSES.get(message.level, 'alert-primary')


@register.simple_tag
def get_class_tag(message):
    return DEFAULT_CLASSES.get(message.level, 'alert-primary')
