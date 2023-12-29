from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)
def send_verification_email(user, request):
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        token = default_token_generator.make_token(user)
        url = request.build_absolute_uri(
            reverse('activate_account', args=[urlsafe_base64_encode(force_bytes(user.pk)), token])
        )
        url = url.replace(request.get_host(), domain)
        # Suponiendo que new_application_notification.txt es tu plantilla de texto plano para la activación
        message = render_to_string('activation_email.txt', {
            'user': user,
            'url': url,
        })

        send_mail(
            'Activación de cuenta',
            message,
            'nikongg22@gmail.com',  # Reemplaza con tu dirección de correo electrónico real
            [user.email],
            fail_silently=False,
        )
        logger.info("Correo de verificación enviado con éxito.")
    except Exception as e:
        logger.error(f"Error al enviar correo de verificación: {e}")