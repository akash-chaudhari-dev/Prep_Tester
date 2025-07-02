from django import template
from Test_Interface.models import Subject

register = template.Library()

@register.inclusion_tag('Test_Interface/sidebar_left.html')
def show_sidebar():
    subjects = Subject.objects.all()
    return {'subjects': subjects}
