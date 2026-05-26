# expenses/templatetags/expense_filters.py

from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """
    Splits a string by a delimiter and returns a list.
    Usage: {{ "a,b,c"|split:"," }}
    Returns: ['a', 'b', 'c']
    """
    return value.split(delimiter)


@register.filter
def abs_value(value):
    """
    Returns the absolute value of a number.
    Usage: {{ negative_number|abs_value }}
    """
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def currency(value):
    """
    Formats a number as Indian currency.
    Usage: {{ 1500.5|currency }} → ₹1,500.50
    """
    try:
        return f'₹{float(value):,.2f}'
    except (TypeError, ValueError):
        return value