from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def is_gestor(user):
    return user.groups.filter(name='gestor').exists() or user.is_superuser