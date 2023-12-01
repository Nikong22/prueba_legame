# context_processors.py dentro de tu aplicación 'accounts'

def user_context(request):
    from .views import get_user_type# Importa la función desde views.py

    user_type = get_user_type(request.user) if request.user.is_authenticated else None

    return {
        'user_type': user_type,
    }
