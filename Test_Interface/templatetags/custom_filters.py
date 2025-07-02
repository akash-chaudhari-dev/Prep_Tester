from django import template
register = template.Library()

@register.filter
def get_option(question, idx):
    return getattr(question, f'option{idx}', '')
