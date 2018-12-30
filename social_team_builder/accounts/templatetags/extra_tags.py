from django import template
from django.utils.safestring import mark_safe
import markdown2


register = template.Library()


@register.filter('mark_down')
def mark_down(text):
    html_body = markdown2.markdown(text)
    return mark_safe(html_body)
