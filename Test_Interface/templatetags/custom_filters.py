# Test_Interface/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_option(question, index):
    """
    Retrieves the option text for a given question and index (1-4).
    Usage: {{ question|get_option:'1' }}
    """
    options = {
        '1': question.option1,
        '2': question.option2,
        '3': question.option3,
        '4': question.option4,
    }
    return options.get(str(index), '')