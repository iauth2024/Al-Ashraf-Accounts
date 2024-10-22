# yourapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='indian_number_format')
def indian_number_format(value):
    try:
        # Convert the value to a float, if possible
        value = float(value)
    except (ValueError, TypeError):
        return value  # If the value is invalid, return it as is

    # Split the value into integer and decimal parts
    value_str = f"{value:.2f}"  # Ensure 2 decimal places
    integer_part, decimal_part = value_str.split('.')

    # Reverse the integer part for grouping
    integer_part = integer_part[::-1]

    # Create groups based on Indian number format rules (first 3 digits, then groups of 2)
    grouped_integer = [integer_part[:3]]  # First group of 3 digits
    for i in range(3, len(integer_part), 2):
        grouped_integer.append(integer_part[i:i+2])  # Group every 2 digits

    # Reverse back and join with commas
    formatted_integer = ','.join(grouped_integer)[::-1]

    # Combine integer and decimal parts
    return f"{formatted_integer}.{decimal_part}"
