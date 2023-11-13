from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Agrega aquí campos adicionales, como:
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()

    def __str__(self):
        return self.company_name


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Campos adicionales específicos para administradores, si son necesarios
    admin_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.user.username
