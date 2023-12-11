from django import template

register = template.Library()

@register.filter(name='make_initials')
def make_initials(value):
    words = value.split()
    initials = [word[0:2].upper() for word in words if word]  # Tomar las dos primeras letras de cada palabra
    return ''.join(initials)

