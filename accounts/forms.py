from django import forms
from .models import JobPost
from .models import Company
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.forms import ModelForm
from .models import BlogEntry

class BlogEntryForm(ModelForm):
    class Meta:
        model = BlogEntry
        fields = ['title', 'content']

class JobPostForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[('AR', 'Argentina'), ('IT', 'Italia')], required=True)
    # Asumiendo que tienes campos province y city en tu modelo JobPost
    # Deberías tener una lógica para poblar estos campos basados en la elección de country

    class Meta:
        model = JobPost
        fields = ['title', 'country', 'province', 'city', 'type', 'category']
        widgets = {
            'province': forms.Select(attrs={'onchange': 'updateCities()'}),
            'city': forms.Select(),
        }

class CompanySignUpForm(UserCreationForm):
    company_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=True)
    address = forms.CharField(required=True)
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa una dirección de email válida.')
    province = forms.CharField(required=True)  # Requerido=False si deseas que sea opcional
    city = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 'phone_number', 'address', 'province', 'city')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            company = Company(
                user=user, 
                company_name=self.cleaned_data['company_name'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                province=self.cleaned_data['province'],
                city=self.cleaned_data['city']
            )
            company.save()
        return user
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['cv']