from django import forms
from .models import JobPost
from .models import Company
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'location', 'type', 'category']

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