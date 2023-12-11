from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone



CANTIDAD_EMPLEADOS_CHOICES = [
    ('1-10', 'Entre 1 y 10'),
    ('11-50', 'Entre 11 y 50'),
    ('51-150', 'Entre 51 y 150'),
    ('151-300', 'Entre 151 y 300'),
    ('301-500', 'Entre 301 y 500'),
    ('501-1000', 'Entre 501 y 1000'),
    ('1001-más', 'Más de 1000'),
]

CATEGORY_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
    ]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)  # Nuevo campo para el nombre
    lastname = models.CharField(max_length=100, blank=True)  # Nuevo campo para el apellido
    email = models.EmailField(unique=True)  # Asegura que el email sea único
    phone_number = PhoneNumberField(blank=True, help_text='Número de teléfono con prefijo internacional')
    bio = models.TextField(blank=True)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    GENDER_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('No Binario', 'No Binario'),
    ]
    genero = models.CharField(max_length=12, choices=GENDER_CHOICES, blank=True)
    DOCUMENT_TYPE_CHOICES = [
        ('DNI', 'DNI'),
        ('CI', 'CI'),
        ('LE', 'LE'),
        ('LC', 'LC'),
        ('PASSPORT', 'Pasaporte'),
    ]
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES, blank=True)
    document_number = models.CharField(max_length=20, blank=True, unique=True)  # Asegura que la documentación sea única
    User.add_to_class('email_confirmed', models.BooleanField(default=False))

    
    def __str__(self):
        return f'{self.name} {self.lastname} - {self.user.username}'



class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    company_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    province_name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True, verbose_name='Categoría')
    razón_social = models.CharField(max_length=100)  # Nuevo campo para la razón social
    cantidad_empleados = models.CharField(max_length=50, choices=CANTIDAD_EMPLEADOS_CHOICES)
    cuit = models.CharField(max_length=13, unique=True)  # Incluye los guiones en la longitud máxima

    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='inactive')

    def __str__(self):
        return self.company_name


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Campos adicionales específicos para administradores, si son necesarios
    admin_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.user.username

#Pantalla para publicaciones de empresas

class JobPost(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    sector  = models.CharField(max_length=50)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='full-time')
    country = models.CharField(max_length=2, choices=[('AR', 'Argentina'), ('IT', 'Italia')])
    province_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True)  # Campo nuevo para la descripción
    application_limit = models.PositiveIntegerField(default=10)  # Un valor por defecto de 10
    expiration_date = models.DateField("Fecha de vencimiento", default=timezone.now)
    address = models.CharField(max_length=255, blank=True)  # Nuevo campo para la dirección

    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')
    def __str__(self):
        return self.title


class BlogEntry(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    
class Application(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='applications')
    applied_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user_profile} se ha postulado a {self.job}'
    
    
    
class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    device_identifier = models.CharField(max_length=255) # Identificador del dispositivo
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class FAQ(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title
    

class Question(models.Model):
    title = models.CharField(max_length=200)
    short_answer = models.TextField()
    complete_answer = models.TextField()
    # Si decides agregar respuestas completas en el futuro, puedes incluir otro campo aquí.

    def __str__(self):
        return self.title