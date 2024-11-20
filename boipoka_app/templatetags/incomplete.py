
from django import template

register = template.Library()

@register.filter
def get_unread(dictionary, key):
    return dictionary.get(key)