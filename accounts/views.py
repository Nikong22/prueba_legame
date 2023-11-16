from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from .models import UserProfile, Company, AdminUser
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages  # Importa la librería de mensajes
from .models import Company
from django.http import HttpResponseForbidden



# ... el resto de tu código ...


# Create your views here.

def login_view(request):
    return render(request, 'login/index.html')

def signup_user(request):
    if request.method == 'GET':
        form = UserCreationForm()
        return render(request, 'login/signup_user.html', {'form': form})
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(username=request.POST.get('username'),
                                                password=request.POST.get('password1'))
                user.save()

                # Crear y guardar el perfil de usuario
                user_profile = UserProfile(user=user)
                # Agrega aquí la lógica para otros campos si es necesario
                user_profile.save()

                login(request, user)
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/signup_user.html', {
                    'form': UserCreationForm(),
                    'error': 'Ya existe un usuario con ese nombre'
                })
        else:
            return render(request, 'login/signup_user.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })

        
def signup_comp(request):
    if request.method == 'GET':
        return render(request, 'login/signup_comp.html', {'form': UserCreationForm()})
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(username=request.POST.get('username'),
                                                password=request.POST.get('password1'))
                user.save()

                # Crear y guardar la entidad de la empresa
                company = Company(user=user, company_name=request.POST.get('company_name'),
                                  address=request.POST.get('address'), 
                                  contact_email=request.POST.get('contact_email'))
                company.save()
                login(request, user)
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/signup_comp.html', {
                    'form': UserCreationForm(),
                    'error': 'Ya existe un usuario con ese nombre'
                })
        else:
            return render(request, 'login/signup_comp.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden'
            })

            
def signup_admin(request):
    if request.method == 'GET':
        return render(request, 'login/signup_admin.html', {'form': UserCreationForm()})
    else:
        if request.POST.get('password1') == request.POST.get('password2'):
            try:
                user = User.objects.create_user(
                    username=request.POST.get('username'),
                    password=request.POST.get('password1')
                )
                # Establecer el usuario como miembro del staff y superusuario
                user.is_staff = True
                user.is_superuser = True
                user.save()

                # Crear y guardar la entidad del administrador
                admin_user = AdminUser(user=user, admin_code=request.POST.get('admin_code'))
                admin_user.save()
                login(request, user)
                return redirect('/')
            except IntegrityError:
                return render(request, 'login/signup_admin.html', {
                    'form': UserCreationForm(),
                    'error': 'Ya existe un usuario con ese nombre'
                })
        else:
            return render(request, 'login/signup_admin.html', {
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verifica si el usuario tiene un perfil en UserProfile
            try:
                UserProfile.objects.get(user=user)
                login(request, user)
                return redirect('/')
            except UserProfile.DoesNotExist:
                # Si no tiene perfil, no es un usuario de signup_user
                pass

        # Si la autenticación falla o no es un usuario de signup_user
        return render(request, 'login/signin_user.html', {
            'form': AuthenticationForm(),
            'error': 'Acceso restringido o usuario/contraseña incorrecta'
        })
        
def signin_comp(request):
    if request.method == 'GET':
        return render(request, 'login/signin_comp.html', {
            'form': AuthenticationForm()
        })
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verifica si el usuario tiene un perfil en Company
            try:
                Company.objects.get(user=user)
                login(request, user)
                return redirect('/')
            except Company.DoesNotExist:
                pass

        return render(request, 'login/signin_comp.html', {
            'form': AuthenticationForm(),
            'error': 'Acceso restringido o usuario/contraseña incorrecta'
        })

    
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

def signin_admin(request):
    if request.method == 'GET':
        return render(request, 'login/signin_admin.html', {
            'form': AuthenticationForm()
        })
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)

            # Imprimir en la consola el estado del usuario
            print(f"Usuario Autenticado: {user.is_authenticated}")
            print(f"Es Staff: {user.is_staff}")
            print(f"Es Superusuario: {user.is_superuser}")

            return redirect('/')
        else:
            return render(request, 'login/signin_admin.html', {
                'form': AuthenticationForm(),
                'error': 'Acceso restringido o usuario/contraseña incorrecta'
            })



def manage_companies(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("No tienes permiso para acceder a esta página.", status=403)

    # Inicializamos las variables de filtrado con los valores de los parámetros GET, si existen.
    name_query = request.GET.get('name', '')
    status_query = request.GET.get('status', '')

    # Iniciamos con todas las empresas.
    companies = Company.objects.all()

    # Filtramos por nombre si el parámetro 'name' está presente.
    if name_query:
        companies = companies.filter(company_name__icontains=name_query)

    # Filtramos por estado si el parámetro 'status' está presente.
    if status_query:
        companies = companies.filter(status=status_query)

    # Pasamos las empresas filtradas al contexto del template.
    context = {
        'companies': companies
    }
    return render(request, 'admin/manage_companies.html', context)

def change_company_status(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    if company.status == 'active':
        company.status = 'inactive'
    else:
        company.status = 'active'
    company.save()
    return redirect('manage_companies')

