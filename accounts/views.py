import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import  transaction, IntegrityError
from django.contrib.auth import login, logout, authenticate
from .models import UserProfile, Company, AdminUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages  # Importa la librería de mensajes
from django.http import HttpResponseForbidden
from .forms import JobPostForm, CompanySignUpForm, UserProfileForm, BlogEntryForm, CustomUserCreationForm
from .models import JobPost, BlogEntry, Application
from django.contrib.staticfiles import finders
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

def faqs(request):
    
    return render(request, 'admin/faqs.html')


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
    latest_entry = BlogEntry.objects.order_by('-updated_at').first()  # Obtén la última entrada del blog
    context = {
        'jobs': active_jobs,
        'latest_entry': latest_entry  # Asegúrate de pasar 'latest_entry' al contexto
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
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'GET':
        form = CustomUserCreationForm()
        return render(request, 'login/signup_user.html', {'form': form})
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile(
                user=user, 
                name=form.cleaned_data.get('name'),
                lastname=form.cleaned_data.get('lastname'),
                email=form.cleaned_data.get('email'),
                phone_number=request.POST.get('phone_number'),  # Captura el número de teléfono del formulario
                bio=request.POST.get('bio'),
                # Agrega aquí la lógica para otros campos si es necesario
            )
            user_profile.save()
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login/signup_user.html', {'form': form})





def signup_comp(request):
    if request.user.is_authenticated:
        return redirect('/')

    sectors_json_path = finders.find('accounts/lista/sectores.json')
    provinces_json_path = finders.find('accounts/argentina/provincias.json')
    cities_json_path = finders.find('accounts/argentina/localidades.json')

    sector_choices, provinces, province_to_cities_map = load_static_data(
        sectors_json_path, provinces_json_path, cities_json_path
    )

    if request.method == 'POST':
        form = CompanySignUpForm(request.POST)
        form.fields['sector'].choices = sector_choices
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    user.refresh_from_db()  # Actualiza la instancia del usuario

                    # Aquí puedes agregar lógica adicional si necesitas crear un perfil de usuario

                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    return redirect('/')
            except IntegrityError as e:
                messages.error(request, f'Hubo un error al crear la cuenta: {e}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CompanySignUpForm()
        form.fields['sector'].choices = sector_choices

    context = {
        'form': form,
        'provinces': provinces,
        'province_to_cities_map': province_to_cities_map
    }
    return render(request, 'login/signup_comp.html', context)


def load_static_data(sectors_path, provinces_path, cities_path):
    # Carga de sectores
    with open(sectors_path, 'r', encoding='utf-8') as sectors_file:
        sectors_data = json.load(sectors_file)['sectores']
    sector_choices = [(sector['nombre'], sector['nombre']) for sector in sectors_data]

    # Carga de provincias
    with open(provinces_path, 'r', encoding='utf-8') as provinces_file:
        provinces_data = json.load(provinces_file)
    provinces = provinces_data['provincias']

    # Carga de ciudades y creación del mapeo de provincias a localidades
    province_to_cities_map = {}
    with open(cities_path, 'r', encoding='utf-8') as cities_file:
        cities_data = json.load(cities_file)
        for city in cities_data['localidades']:
            province_id = city['provincia']['id']
            if province_id not in province_to_cities_map:
                province_to_cities_map[province_id] = []
            province_to_cities_map[province_id].append(city['nombre'])

    return sector_choices, provinces, province_to_cities_map


def load_sectors(request):
    json_path = finders.find('accounts/lista/sectores.json')
    if json_path:
        with open(json_path, 'r', encoding='utf-8') as file:
            sectors = json.load(file)
        return JsonResponse(sectors)
    else:
        return JsonResponse({'error': 'Archivo de sectores no encontrado'}, status=404)

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
    if not hasattr(request.user, 'company') or request.user.company.status != 'active':
        return HttpResponseForbidden("No tienes permiso para crear una publicación de trabajo.")

    # Carga de sectores desde el archivo JSON
    json_path = finders.find('accounts/lista/sectores.json')
    with open(json_path, 'r', encoding='utf-8') as sectors_file:
        sectors_data = json.load(sectors_file)
    sector_choices = [(sector['nombre'], sector['nombre']) for sector in sectors_data['sectores']]

    # Carga de datos de provincias y ciudades
    provinces, province_to_cities_map = load_provinces_and_cities()

    form = JobPostForm(request.POST or None)
    form.fields['sector'].choices = sector_choices  # Actualizar dinámicamente los sectores

    if request.method == 'POST' and form.is_valid():
        job_post = form.save(commit=False)
        job_post.company = request.user.company
        job_post.save()
        messages.success(request, "La publicación de trabajo ha sido creada con éxito.")
        return redirect('my_job_list')
    
    user_type = get_user_type(request.user)

    # Añade user_type al contexto
    context = {
        'form': form,
        'provinces': provinces,
        'province_to_cities_map': province_to_cities_map,
        'user_type': user_type,  # Añadido aquí
    }   
    return render(request, 'jobs/create_job_post.html', context)

def load_provinces_and_cities():
    # Carga de datos de provincias
    provinces_json_path = finders.find('accounts/argentina/provincias.json')
    with open(provinces_json_path, 'r', encoding='utf-8') as provinces_file:
        provinces_data = json.load(provinces_file)['provincias']
    
    # Carga de ciudades y creación del mapeo de provincias a localidades
    province_to_cities_map = {}
    cities_json_path = finders.find('accounts/argentina/localidades.json')
    with open(cities_json_path, 'r', encoding='utf-8') as cities_file:
        cities_data = json.load(cities_file)
        for city in cities_data['localidades']:
            province_id = city['provincia']['id']
            if province_id not in province_to_cities_map:
                province_to_cities_map[province_id] = []
            province_to_cities_map[province_id].append(city['nombre'])

    return provinces_data, province_to_cities_map


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
        'user': request.user,
        'user_info': user_info,
        'user_type': user_type,
    }
    return render(request, 'profile/my_profile.html', context)

@login_required
def upload_cv(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            # Guarda el formulario, pero no hagas commit todavía para que puedas actualizar manualmente
            # los campos phone_number y bio con los valores actuales si no se proporcionan nuevos.
            user_profile_instance = form.save(commit=False)
            user_profile_instance.phone_number = request.POST.get('phone_number', user_profile.phone_number)
            user_profile_instance.bio = request.POST.get('bio', user_profile.bio)
            user_profile_instance.save()
            messages.success(request, 'CV subido con éxito.')
            return redirect('my_profile')
        else:
            # Si el formulario no es válido, puedes elegir manejar los errores aquí
            pass
    else:
        form = UserProfileForm(instance=request.user.userprofile)

    context = {
        'cv_form': form,
    }
    return render(request, 'profile/my_profile.html', context)

@login_required
def upload_profile_picture(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen de perfil actualizada.')
        else:
            messages.error(request, 'Error al actualizar la imagen de perfil.')
        return redirect('my_profile')

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_superuser  # Cambia is_admin por is_superuser

@login_required
@user_passes_test(is_admin)
def admin_blog(request):
    # Suponiendo que solo hay una entrada que actúa como la principal
    entry = BlogEntry.objects.first() or BlogEntry()  # Obtén la primera entrada o crea una nueva si no hay ninguna
    if request.method == 'POST':
        form = BlogEntryForm(request.POST, instance=entry)  # Asegúrate de pasar la instancia existente para actualizar
        if form.is_valid():
            form.save()
            messages.success(request, 'La entrada del blog ha sido actualizada con éxito.')
            return redirect('admin_blog')  # Redirige para evitar el envío doble del formulario
    else:
        form = BlogEntryForm(instance=entry)
    return render(request, 'admin/admin_blog.html', {'form': form})



@csrf_exempt
def update_user_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            user = request.user

            # Verifica si el nombre de usuario nuevo ya existe
            new_username = data.get('username')
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({'status': 'error', 'message': 'El nombre de usuario ya existe'})

            # Actualiza UserProfile
            if hasattr(user, 'userprofile'):
                user_profile = user.userprofile
                user_profile.phone_number = data.get('phone_number', user_profile.phone_number)
                user_profile.bio = data.get('bio', user_profile.bio)
                user_profile.save()

            # Actualiza Company (incluido el campo address)
            if hasattr(user, 'company'):
                company_profile = user.company
                company_profile.company_name = data.get('company_name', company_profile.company_name)
                company_profile.phone_number = data.get('phone_number', company_profile.phone_number)
                company_profile.address = data.get('address', company_profile.address)
                company_profile.sector = data.get('sector', company_profile.sector)
                company_profile.cantidad_empleados = data.get('cantidad_empleados', company_profile.cantidad_empleados)
                company_profile.razón_social = data.get('razón_social', company_profile.razón_social)
                company_profile.save()

            # Actualiza el nombre de usuario
            if new_username and new_username != user.username:
                user.username = new_username
                user.save()

            return JsonResponse({'status': 'success', 'message': 'Datos actualizados con éxito'})
        except json.JSONDecodeError as e:
            return JsonResponse({'status': 'error', 'message': f'Error al decodificar JSON: {str(e)}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al actualizar los datos: {str(e)}'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'})



def job_details(request, job_id):
    job = get_object_or_404(JobPost, pk=job_id)
    return render(request, 'jobs/job_details.html', {'job': job})

def id_to_province_name(province_id):
    # Encuentra la ruta completa al archivo JSON en tus archivos estáticos
    json_path = finders.find('accounts/argentina/provincias.json')
    
    # Asegúrate de manejar el caso en el que el archivo no se encuentre
    if not json_path:
        return None

    # Carga los datos del JSON
    with open(json_path, 'r', encoding='utf-8') as file:
        provinces_data = json.load(file)
    
    # Busca el nombre de la provincia correspondiente al ID
    for province in provinces_data['provincias']:
        if str(province['id']) == str(province_id):
            return province['nombre']
    
    # Si no se encuentra la provincia, devuelve None o una cadena vacía
    return None

def is_company_user(user):
    return hasattr(user, 'company') and user.company is not None


@login_required
@user_passes_test(is_company_user)
def edit_job_post(request, job_id):
    job = get_object_or_404(JobPost, pk=job_id, company=request.user.company)

    if request.method == 'POST':
        print(request.body)  # Agrega esta línea para depurar
        try:
            data = json.loads(request.body)
            job.title = data.get('title', job.title)
            job.descripcion = data.get('descripcion', job.descripcion)
            job.category = data.get('category', job.category)
            job.save()
            return JsonResponse({'status': 'success', 'message': 'Publicación actualizada correctamente'})
        except json.JSONDecodeError as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        form = JobPostForm(instance=job)
        return render(request, 'jobs/edit-job.html', {'form': form, 'job': job})



@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(JobPost, pk=job_id)
    user_profile = request.user.userprofile

    # Verifica si el usuario ya se ha postulado para evitar duplicados
    if not Application.objects.filter(job=job, user_profile=user_profile).exists():
        Application.objects.create(job=job, user_profile=user_profile)
        # Agrega aquí cualquier lógica adicional, como enviar un correo electrónico de confirmación

    return redirect('job_details', job_id=job_id)