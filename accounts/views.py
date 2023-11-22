import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from .models import UserProfile, Company, AdminUser
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Importa la librería de mensajes
from .models import Company
from django.http import HttpResponseForbidden
from .forms import JobPostForm, CompanySignUpForm
from .models import JobPost
from django.contrib.staticfiles import finders
from .forms import UserProfileForm


# ... el resto de tu código ...


# Create your views here.

def get_user_type(user):
    if hasattr(user, 'userprofile'):
        return 'Usuario'
    elif hasattr(user, 'company'):
        return 'Empresa'
    elif user.is_staff or user.is_superuser:
        return 'Admin'
    else:
        return None

def login_view(request):
    active_jobs = JobPost.objects.filter(status='active')
    context = {
        'jobs': active_jobs
    }
    if request.user.is_authenticated:
        context['username'] = request.user.username
        if hasattr(request.user, 'userprofile'):
            context['user_type'] = 'Usuario'
        elif hasattr(request.user, 'company'):
            context['user_type'] = 'Empresa'
        elif request.user.is_staff or request.user.is_superuser:
            context['user_type'] = 'Admin'
        else:
            context['user_type'] = 'Tipo de usuario no definido'
    return render(request, 'login/index.html', context)

def signup_user(request):
    # Si el usuario ya está autenticado, redirígelo a la página de inicio o donde prefieras
    if request.user.is_authenticated:
        return redirect('/')
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
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = CompanySignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Aquí puedes añadir la lógica para iniciar sesión automáticamente al usuario
            return redirect('login_view')
    else:
        form = CompanySignUpForm()

    # Encuentra la ubicación del archivo JSON en tus archivos estáticos
    json_path = finders.find('accounts/argentina/provincias.json')
    provinces = []
    if json_path:
        with open(json_path, 'r', encoding='utf-8') as f:
            provinces_json = json.load(f)
            provinces = provinces_json.get('provincias', [])
    else:
        print("Archivo JSON de provincias no encontrado.")

    # Cargar localidades
    cities_json_path = finders.find('accounts/argentina/localidades.json')
    if cities_json_path:
        with open(cities_json_path, 'r', encoding='utf-8') as f:
            cities_json = json.load(f)
        cities = cities_json['localidades']
    else:
        cities = []

    # Mapeo de provincias a localidades
    province_to_cities_map = {}
    for localidad in cities_json['localidades']:
        provincia_id = localidad['provincia']['id']
        if provincia_id not in province_to_cities_map:
            province_to_cities_map[provincia_id] = []
        province_to_cities_map[provincia_id].append(localidad['nombre'])

    return render(request, 'login/signup_comp.html', {'form': form, 'provinces': provinces, 'cities': cities, 'province_to_cities_map': province_to_cities_map})
   

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
    if request.user.is_authenticated:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    if request.method == 'GET':
        return render(request, 'login/signin.html', {'form': AuthenticationForm()})
    else:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Comprobar si el usuario es un administrador y rechazar el inicio de sesión
            if user.is_superuser:
                messages.error(request, 'El inicio de sesión no está permitido.')
                return render(request, 'login/signin.html', {
                    'form': AuthenticationForm()
                })
            
            login(request, user)
            # Redireccionar a la página de inicio de la empresa o del usuario según el tipo
            if hasattr(user, 'company'):
                return redirect('/')  
            else:
                return redirect('/')  
        else:
            messages.error(request, 'Acceso restringido o usuario/contraseña incorrecta')
            return render(request, 'login/signin.html', {
                'form': AuthenticationForm()
            })

def signin_admin(request):
    if request.user.is_authenticated:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
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

def company_details(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    return render(request, 'admin/company_details.html', {'company': company})

def activate_company(request, company_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden()

    company = get_object_or_404(Company, pk=company_id)
    if company.status == 'inactive':
        company.status = 'active'
        company.save()
        messages.success(request, 'La empresa ha sido activada con éxito.')
    return redirect('company_details', company_id=company_id)

def inactivate_company(request, company_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden()

    company = get_object_or_404(Company, pk=company_id)
    if company.status == 'active':
        company.status = 'inactive'
        company.save()
        JobPost.objects.filter(company=company).update(status='inactive')
        messages.success(request, 'La empresa ha sido inactivada con éxito.')
    return redirect('company_details', company_id=company_id)

@login_required
def create_job_post(request):
    if not hasattr(request.user, 'company'):
        return HttpResponseForbidden("No tienes permiso para crear una publicación de trabajo.")

    user_type = get_user_type(request.user)
    form = JobPostForm(request.POST or None)

    # Encuentra la ubicación del archivo JSON en tus archivos estáticos
    provinces_json_path = finders.find('accounts/argentina/provincias.json')
    cities_json_path = finders.find('accounts/argentina/localidades.json')
    provinces = []
    cities = []
    province_to_cities_map = {}

    # Carga las provincias y ciudades de los archivos JSON
    if provinces_json_path and cities_json_path:
        with open(provinces_json_path, 'r', encoding='utf-8') as f:
            provinces = json.load(f).get('provincias', [])
        
        with open(cities_json_path, 'r', encoding='utf-8') as f:
            cities = json.load(f).get('localidades', [])
        
        # Crea un mapeo de provincias a localidades
        for localidad in cities:
            provincia_id = localidad['provincia']['id']
            if provincia_id not in province_to_cities_map:
                province_to_cities_map[provincia_id] = []
            province_to_cities_map[provincia_id].append(localidad['nombre'])

    if request.method == 'POST' and form.is_valid():
        job_post = form.save(commit=False)
        job_post.company = request.user.company
        # Asegúrate de capturar y asignar los campos de país, provincia y ciudad aquí
        job_post.save()
        messages.success(request, "El trabajo ha sido publicado con éxito.")
        return redirect('my_job_list')
    
    return render(request, 'jobs/create_job_post.html', {
        'form': form,
        'user_type': user_type,
        'provinces': provinces,
        'province_to_cities_map': province_to_cities_map
    })

@login_required
def my_job_list(request):
    user_type = get_user_type(request.user)
    jobs = JobPost.objects.filter(company=request.user.company)
    if not hasattr(request.user, 'company'):
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

    jobs = JobPost.objects.filter(company=request.user.company)
    return render(request, 'jobs/my_job_list.html', {'jobs': jobs, 'user_type': user_type})

@login_required
def delete_job_post(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, company=request.user.company)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "La publicación de trabajo ha sido eliminada.")
        return redirect('my_job_list')
    return render(request, 'jobs/confirm_delete.html', {'job': job})

@login_required
def toggle_job_post_status(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, company=request.user.company)
    if request.method == 'POST':
        job.status = 'active' if job.status == 'inactive' else 'inactive'
        job.save()
        messages.success(request, f"El estado de la publicación de trabajo ha sido cambiado a {job.status}.")
        return redirect('my_job_list')
    return redirect('my_job_list')

# Perfil del usuario
@login_required
def my_profile(request):
    user_type = get_user_type(request.user)
    if user_type == 'Empresa':
        user_info = request.user.company
    elif user_type == 'Usuario':
        user_info = request.user.userprofile
    else:
        user_info = None  # O manejar como prefieras si no es ninguno de los dos

    context = {
        'user_info': user_info,
        'user_type': user_type,
    }
    return render(request, 'profile/my_profile.html', context)

def upload_cv(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'CV subido con éxito.')
            return redirect('some_view_name')  # Reemplaza con el nombre de la vista a la que deseas redirigir después de la carga
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'some_template.html', {'form': form})  # Asegúrate de usar la plantilla correcta