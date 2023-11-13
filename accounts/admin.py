from django.contrib import admin
from .models import UserProfile, Company, AdminUser  # Asegúrate de importar tus modelos
  

admin.site.register(UserProfile)
admin.site.register(Company)
admin.site.register(AdminUser)
