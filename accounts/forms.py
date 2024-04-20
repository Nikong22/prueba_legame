from django import forms
from .models import JobPost, Company, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import BlogEntry
from .models import CANTIDAD_EMPLEADOS_CHOICES
from django.core.validators import RegexValidator
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from django.contrib.staticfiles import finders
from django.contrib.auth.forms import AuthenticationForm
from .models import FAQ 
from .models import Question
from .utils import id_to_province_name
from .models import AdminUser
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.urls import reverse
from smtplib import SMTPException
from django.core.mail import send_mail
from .email_utils import send_verification_email
import logging
from django.db import transaction
from .models import FAQTranslation
from .models import QuestionTranslation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger(__name__)



# Asegúrate de incluir esta línea

import re
import json



CATEGORY_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
    ]

    


class BlogEntryForm(forms.ModelForm):
    title_es = forms.CharField(max_length=200, required=False)  # Agregar required=False si el campo puede estar vacío
    content_es = forms.CharField(widget=forms.Textarea, required=False)
    title_it = forms.CharField(max_length=200, required=False)
    content_it = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = BlogEntry
        fields = ['title', 'content', 'title_es', 'content_es', 'title_it', 'content_it']
        
    def __init__(self, *args, **kwargs):
        super(BlogEntryForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control mi-clase-adicional'})
        self.fields['content'].widget.attrs.update({'class': 'form-control mi-clase-adicional'})



class JobPostForm(forms.ModelForm):
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=True)
    expiration_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    sector = forms.ChoiceField(choices=[])
    region_it = forms.CharField(max_length=100, required=False)
    provincia_it = forms.CharField(max_length=100, required=False)
    comuna_it = forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=2, required=True)  # Ejemplo, ajusta según sea necesario
    class Meta:
        model = JobPost
        fields = ['title', 'country', 'province_name', 'city', 'sector', 'region_it', 'provincia_it', 'comuna_it', 'category', 'descripcion', 'application_limit', 'expiration_date', 'address']
        widgets = {
            'province': forms.Select(attrs={'onchange': 'updateCities()'}),
            'city': forms.Select(),
            'sector': forms.Select(),
            'category': forms.Select(),  # Asegúrate de que el campo 'category' use un widget de selección
        }
    
    def __init__(self, *args, **kwargs):
        super(JobPostForm, self).__init__(*args, **kwargs)
        self.fields['sector'].choices = self.load_sector_choices()
    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get("country")

        if country == "IT":
            # Para Italia, no requerimos province_name, así que lo establecemos en blanco o nulo
            cleaned_data['province_name'] = None
        else:
            # Para otros países, asegúrate de que province_name esté presente
            if not cleaned_data.get('province_name'):
                self.add_error('province_name', 'Este campo es obligatorio.')

        return cleaned_data    
    def load_sector_choices(self):
        sectors_json_path = finders.find('accounts/lista/sectores.json')
        if sectors_json_path:
            with open(sectors_json_path, 'r', encoding='utf-8') as sectors_file:
                sectors_data = json.load(sectors_file)
            return [(sector['es'], sector['it']) for sector in sectors_data['sectores']]
        else:
            return []

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    lastname = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    genero = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=False)
    document_type = forms.ChoiceField(choices=UserProfile.DOCUMENT_TYPE_CHOICES, required=False)
    document_number = forms.CharField(max_length=20, required=False)
    phone_number = PhoneNumberField(widget=PhoneNumberPrefixWidget(), required=False)


    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'name', 'lastname', 'email', 'password1', 'password2', 'phone_number', 'genero', 'document_type', 'document_number']
    
    def clean_document_number(self):
        document_type = self.cleaned_data.get("document_type")
        document_number = self.cleaned_data.get("document_number")

        if document_type == 'DNI':
            if not re.fullmatch(r'\d{7,8}', document_number):
                raise forms.ValidationError("El DNI debe tener entre 7 y 8 dígitos.")

        elif document_type == 'CI':
            # Ejemplo de validación para CI (ajustar según sea necesario)
            if not document_number.isalnum() or len(document_number) > 10:
                raise forms.ValidationError("Formato de CI no válido.")

        elif document_type in ['LE', 'LC']:
            # Ejemplo de validación para LE y LC
            if not document_number.isdigit():
                raise forms.ValidationError("La LE o LC debe contener solo números.")

        elif document_type == 'PASSPORT':
            if not re.fullmatch(r'[A-Z0-9]{6,9}', document_number):
                raise forms.ValidationError("Formato de pasaporte no válido.")

        return document_number
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email

    def clean_document_number(self):
        document_number = self.cleaned_data.get('document_number')
        if UserProfile.objects.filter(document_number=document_number).exists():
            raise forms.ValidationError("Este número de documento ya está en uso.")
        return document_number
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            send_verification_email(user, self.request)  # Usando la función de utilidad
        return user

class AdminCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. Ingresa una dirección de email válida.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
            AdminUser.objects.create(user=user, email=user.email)
        return user
    
class CompanySignUpForm(UserCreationForm):
    company_name = forms.CharField(required=True)
    phone_number = PhoneNumberField(
        widget=PhoneNumberPrefixWidget(initial='AR'),  # Predeterminado a Argentina
        help_text='Número de teléfono con prefijo internacional'
    )    
    address = forms.CharField(required=True)
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa una dirección de email válida.')
    city = forms.CharField(required=False)
    sector = forms.ChoiceField(choices=[])  # Asegúrate de llenar esta lista dinámicamente si es necesario
    razón_social = forms.CharField(required=True)
    cantidad_empleados = forms.ChoiceField(choices=CANTIDAD_EMPLEADOS_CHOICES, required=True)
    province_name = forms.CharField(max_length=100, required=False)
    cuit = forms.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                r'^\d{2}-\d{8}-\d{1}$',
                message="El CUIT debe tener el formato XX-XXXXXXXX-X."
            )
        ]
    )
     # Campos para Italia
    region_it = forms.CharField(max_length=100, required=False)
    provincia_it = forms.CharField(max_length=100, required=False)
    comuna_it = forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=2, required=True)  # Ejemplo, ajusta según sea necesario



    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'razón_social', 'cantidad_empleados', 'phone_number', 'address', 'city', 'sector', 'province_name', 'region_it', 'provincia_it', 'comuna_it']
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        # Comprueba si el número de teléfono es None
        if phone_number is None:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        # Comprueba si el número de teléfono tiene un código de país válido
        if not str(phone_number.country_code) in ['54', '39']:
            raise forms.ValidationError("Por favor ingresa un número de teléfono válido para Argentina o Italia.")

        return phone_number
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email

    def clean_cuit(self):
        cuit = self.cleaned_data.get('cuit')
        if Company.objects.filter(cuit=cuit).exists():
            raise forms.ValidationError("Este CUIT ya está en uso.")
        return cuit
    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get("country")

        if country == "IT":
            # Valida campos para Italia
            for field_name in ['region_it', 'provincia_it', 'comuna_it']:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, 'Este campo es obligatorio para Italia.')
        elif country == "AR":
            # Valida campos para Argentina
            if not cleaned_data.get('city'):
                self.add_error('city', 'Este campo es obligatorio para Argentina.')
            # Agrega validaciones adicionales para Argentina si es necesario
        else:
            # Maneja otros países o errores
            # Puedes agregar un mensaje de error si el país no está soportado
            pass

        return cleaned_data

    def save(self, commit=True):
        logger.info("Iniciando el método save en CompanySignUpForm")
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            with transaction.atomic():
                user.save()
        return user
    def send_verification_email(self, user, request):
        # Llama a la función global send_verification_email
        send_verification_email(user, request)
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CompanySignUpForm, self).__init__(*args, **kwargs)
        self.fields['sector'].choices = self.load_sector_choices()
        # La lógica para cargar las opciones de 'sector' desde un archivo JSON u otra fuente debe ir aquí
    
    def load_sector_choices(self):
        # Aquí iría tu lógica para cargar las opciones de sector desde un archivo JSON u otra fuente
        return []
    
class UserProfileForm(forms.ModelForm):
    phone_number = PhoneNumberField(
        widget=PhoneNumberPrefixWidget(initial='AR'),  # Predeterminado a Argentina
        help_text='Número de teléfono con prefijo internacional'
    )
    class Meta:
        model = UserProfile
        fields = (
            'name', 'lastname', 'email', 'genero', 'document_type',
            'document_number', 'phone_number', 'bio', 'cv', 'profile_picture'
        )
        # Añade aquí cualquier lógica adicional para campos adicionales si es necesario
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and phone_number.country_code not in ['54', '39']:  # Códigos de país para AR y IT
            raise forms.ValidationError("Por favor ingresa un número de teléfono válido para Argentina o Italia.")
        return phone_number
    
    
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'id': 'username', 'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password', 'class': 'form-control', 'placeholder': 'Password'}))

class FAQForm(forms.ModelForm):
    title_es = forms.CharField(max_length=200, required=False, label="Título ESP")  
    content_es = forms.CharField(widget=forms.Textarea, required=False, label="Contenido ESP")  
    title_it = forms.CharField(max_length=200, required=False, label="Título IT")  
    content_it = forms.CharField(widget=forms.Textarea, required=False, label="Contenido IT")  

    class Meta:
        model = FAQTranslation
        fields = ['title_es', 'content_es', 'title_it', 'content_it']

    def clean(self):
        cleaned_data = super().clean()
        title_es = cleaned_data.get('title_es')
        content_es = cleaned_data.get('content_es')
        title_it = cleaned_data.get('title_it')
        content_it = cleaned_data.get('content_it')

        if title_es and not content_es:
            raise forms.ValidationError({'content_es': 'El contenido en español no puede estar vacío.'})

        if content_es and not title_es:
            raise forms.ValidationError({'title_es': 'El título en español no puede estar vacío.'})

        if title_it and not content_it:
            raise forms.ValidationError({'content_it': 'El contenido en italiano no puede estar vacío.'})

        if content_it and not title_it:
            raise forms.ValidationError({'title_it': 'El título en italiano no puede estar vacío.'})




class QuestionForm(forms.ModelForm):
    title_es = forms.CharField(max_length=200, required=False, label="Título ESP")  
    short_answer_es = forms.CharField(widget=forms.Textarea, required=False, label="Respuesta Corta ESP")  
    complete_answer_es = forms.CharField(widget=forms.Textarea, required=False, label="Respuesta Completa ESP")  
    title_it = forms.CharField(max_length=200, required=False, label="Título IT")  
    short_answer_it = forms.CharField(widget=forms.Textarea, required=False, label="Risposta breve IT")  
    complete_answer_it = forms.CharField(widget=forms.Textarea, required=False, label="Risposta completa IT")  

    class Meta:
        model = QuestionTranslation
        fields = ['title_es', 'short_answer_es', 'complete_answer_es', 'title_it', 'short_answer_it', 'complete_answer_it']

    def clean(self):
        cleaned_data = super().clean()
        title_es = cleaned_data.get('title_es')
        short_answer_es = cleaned_data.get('short_answer_es')
        complete_answer_es = cleaned_data.get('complete_answer_es')
        title_it = cleaned_data.get('title_it')
        short_answer_it = cleaned_data.get('short_answer_it')
        complete_answer_it = cleaned_data.get('complete_answer_it')

        if title_es and not short_answer_es:
            raise forms.ValidationError({'short_answer_es': 'La respuesta corta en español no puede estar vacía.'})

        if short_answer_es and not title_es:
            raise forms.ValidationError({'title_es': 'El título en español no puede estar vacío.'})

        if complete_answer_es and not short_answer_es:
            raise forms.ValidationError({'short_answer_es': 'La respuesta corta en español no puede estar vacía.'})

        if short_answer_es and not complete_answer_es:
            raise forms.ValidationError({'complete_answer_es': 'La respuesta completa en español no puede estar vacía.'})

        if title_it and not short_answer_it:
            raise forms.ValidationError({'short_answer_it': 'La respuesta corta en italiano no puede estar vacía.'})

        if short_answer_it and not title_it:
            raise forms.ValidationError({'title_it': 'El título en italiano no puede estar vacío.'})

        if complete_answer_it and not short_answer_it:
            raise forms.ValidationError({'short_answer_it': 'La respuesta corta en italiano no puede estar vacía.'})

        if short_answer_it and not complete_answer_it:
            raise forms.ValidationError({'complete_answer_it': 'La respuesta completa en italiano no puede estar vacía.'})
        


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        # Enviar correo electrónico aquí
        pass