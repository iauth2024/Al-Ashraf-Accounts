# yourapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def indian_number_format(value):
    try:
        value = int(value)
    except ValueError:
        return value
    return '{:,}'.format(value).replace(',', ',')
