# coding=utf-8
from django.template import Library

register = Library()


@register.filter
def get_item(obj, attr):
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr)


@register.filter
def get_items(dictionary):
    return dictionary.items()
