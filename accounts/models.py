from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Agrega aquí campos adicionales, como:
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    company_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
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
    type = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    country = models.CharField(max_length=2, choices=[('AR', 'Argentina'), ('IT', 'Italia')])
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')
    def __str__(self):
        return self.title
