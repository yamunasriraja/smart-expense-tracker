from django import template

register = template.Library()


@register.filter
def percentage(value, total):
    try:
        return round((value / total) * 100, 1)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def split(value, key):
    
    return value.split(key)