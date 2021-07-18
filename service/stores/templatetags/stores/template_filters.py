# coding=utf-8
from django.template import Library

register = Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_items(dictionary):
    return dictionary.items()
