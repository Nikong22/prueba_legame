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




# Asegúrate de incluir esta línea

import re
import json



CATEGORY_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
    ]

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
    def send_verification_email(self, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = self.request.build_absolute_uri(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))
        message = render_to_string('activation_email.html', {
            'user': user,
            'url': url,
        })
        send_mail(
            'Activación de cuenta',
            message,
            'algo@progettolegame.com',
            [user.email],
            fail_silently=False,
        )
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            self.send_verification_email(user)  # Aquí llamas al método para enviar el email

        return user

class BlogEntryForm(ModelForm):
    class Meta:
        model = BlogEntry
        fields = ['title', 'content']

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
            return [(sector['nombre'], sector['nombre']) for sector in sectors_data['sectores']]
        else:
            return []

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
        if str(phone_number.country_code) in ['54', '39']:
            print("El código de país es válido")
        else:
            print("El código de país no es válido")
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
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            province_id = self.cleaned_data.get('province_name', '')
            province_name = id_to_province_name(province_id) if province_id else ''
            # Aquí, simplemente usamos los campos proporcionados por el modelo Company
            company = Company(
                user=user, 
                company_name=self.cleaned_data['company_name'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                sector=self.cleaned_data['sector'],
                razón_social=self.cleaned_data['razón_social'],
                cantidad_empleados=self.cleaned_data['cantidad_empleados'],
                contact_email=self.cleaned_data['email'],
                cuit=self.cleaned_data['cuit'],
                province_name=province_name,  # Asigna aquí el nombre de la provincia
                region_it=self.cleaned_data['region_it'],
                provincia_it=self.cleaned_data['provincia_it'],
                comuna_it=self.cleaned_data['comuna_it']
                
            )

            company.save()
        return user
    
    def __init__(self, *args, **kwargs):
        super(CompanySignUpForm, self).__init__(*args, **kwargs)
        # La lógica para cargar las opciones de 'sector' desde un archivo JSON u otra fuente debe ir aquí
        self.fields['sector'].choices = self.load_sector_choices()
    
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
    class Meta:
        model = FAQ
        fields = ['title', 'content']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'short_answer', 'complete_answer']

