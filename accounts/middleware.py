# myapp/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from .models import UserSession  # Asegúrate de importar UserSession desde tus modelos

class OneSessionPerUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            current_session_key = request.session.session_key
            if not UserSession.objects.filter(user=request.user, session_key=current_session_key).exists():
                logout(request)
