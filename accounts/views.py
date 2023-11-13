from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate

# Create your views here.

def login_view(request):
    return render(request, 'login/index.html')

def signup_user(request):
    if request.method == 'GET':
        form = UserCreationForm()
        return render(request, 'login/login_user.html', {
            'form': form
        })
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(username=request.POST.get('username'),
                                                password=request.POST.get('password1'))
                user.save()
                # Aquí podrías autenticar y loguear al usuario automáticamente
                #return HttpResponse('Usuario creado')
                login(request, user)
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/login_user.html', {
                'form': UserCreationForm(),
                'error': 'Ya existe un usuario con ese nombre'
            })
        else:
            return render(request, 'login/login_user.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })
        
def signup_comp(request):
    if request.method == 'GET':
        return render(request, 'login/login_companies.html', {
            'form': UserCreationForm()
        })
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(username=request.POST.get('username'),
                                                password=request.POST.get('password1'))
                user.save()
                # Aquí podrías autenticar y loguear al usuario automáticamente
                #return HttpResponse('Usuario creado')
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/login_companies.html', {
                'form': UserCreationForm(),
                'error': 'Ya existe un usuario con ese nombre'
            })
        else:
            return render(request, 'login/login_companies.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })
            
def signup_admin(request):
    if request.method == 'GET':
        return render(request, 'login/login_admin.html', {
            'form': UserCreationForm()
        })
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(username=request.POST.get('username'),
                                                password=request.POST.get('password1'))
                user.save()
                # Aquí podrías autenticar y loguear al usuario automáticamente
                #return HttpResponse('Usuario creado')
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/login_admin.html', {
                'form': UserCreationForm(),
                'error': 'Ya existe un usuario con ese nombre'
            })
        else:
            return render(request, 'login/login_admin.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })
            
def signout(request):
        logout(request)
        return redirect('/')

def signin(request):
    if request.method == 'GET':
        return render(request, 'login/signin_user.html', {
            'form': AuthenticationForm()
        })
    else:
        username = request.POST.get('username')  # Usa .get() en lugar de llamar a request.POST como una función
        password = request.POST.get('password')  # Usa .get() en lugar de llamar a request.POST como una función
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login/signin_user.html', {
                'form': AuthenticationForm(),
                'error': 'Usuario o contraseña incorrecta'
            })