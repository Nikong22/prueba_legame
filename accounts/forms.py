from django import forms
from .models import JobPost, Company, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import BlogEntry
from .models import CANTIDAD_EMPLEADOS_CHOICES

CATEGORY_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
    ]

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    lastname = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'name', 'lastname', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class BlogEntryForm(ModelForm):
    class Meta:
        model = BlogEntry
        fields = ['title', 'content']

class JobPostForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[('AR', 'Argentina'), ('IT', 'Italia')], required=True)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=True)
    
    class Meta:
        model = JobPost
        fields = ['title', 'country', 'province', 'city', 'sector', 'category', 'descripcion']
        widgets = {
            'province': forms.Select(attrs={'onchange': 'updateCities()'}),
            'city': forms.Select(),
            'sector': forms.Select(),
            'category': forms.Select(),  # Asegúrate de que el campo 'category' use un widget de selección
        }
    
    def __init__(self, *args, **kwargs):
        super(JobPostForm, self).__init__(*args, **kwargs)
        
        
class CompanySignUpForm(UserCreationForm):
    company_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=True)
    address = forms.CharField(required=True)
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa una dirección de email válida.')
    province = forms.CharField(required=True)
    city = forms.CharField(required=True)
    sector = forms.ChoiceField(choices=[])
    razón_social = forms.CharField(required=True)
    cantidad_empleados = forms.ChoiceField(choices=CANTIDAD_EMPLEADOS_CHOICES, required=True)
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'razón_social', 'cantidad_empleados', 'phone_number', 'address', 'province', 'city', 'sector']
    
    def __init__(self, *args, **kwargs):
        super(CompanySignUpForm, self).__init__(*args, **kwargs)
        # La lógica para cargar las opciones de 'sector' desde un archivo JSON u otra fuente debe ir aquí
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Creación de la instancia de Company y asignación del email a contact_email
            company = Company(
                user=user, 
                company_name=self.cleaned_data['company_name'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                province=self.cleaned_data['province'],
                city=self.cleaned_data['city'],
                sector=self.cleaned_data['sector'],
                razón_social=self.cleaned_data['razón_social'],
                cantidad_empleados=self.cleaned_data['cantidad_empleados'],
                contact_email=self.cleaned_data['email'],  # Asigna el email del formulario al contact_email de Company
            )
            company.save()
        return user
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [ 'cv']