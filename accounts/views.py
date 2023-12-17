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
from django.utils import timezone
from .models import UserSession  # Asegúrate de importar UserSession
from .forms import CustomAuthenticationForm
from django.db.models import Count
from django.core.paginator import Paginator
from .models import FAQ, Question
from .forms import FAQForm, QuestionForm
from django.core.signing import Signer, BadSignature
from django.core.mail import send_mail
from django.urls import reverse
from .utils import id_to_province_name
import os


def faqs(request):
    
    return render(request, 'admin/faqs.html')

def index(request):
    search_query = request.GET.get('search_query', '')
    sector_query = request.GET.get('sector', '')
    country_query = request.GET.get('country', '')
    job_list = JobPost.objects.filter(status='active').order_by('-created_at')  # Asumiendo que 'created_at' es el campo de fecha

    if search_query:
        job_list = job_list.filter(title__icontains=search_query)
    if sector_query:
        job_list = job_list.filter(sector=sector_query)
    if country_query:
        job_list = job_list.filter(country=country_query)

    # Paginación
    paginator = Paginator(job_list, 10)  # Muestra 10 trabajos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sectors = JobPost.objects.values('sector').distinct()
    countries = JobPost.objects.values('country').distinct()
    latest_entry = BlogEntry.objects.order_by('-updated_at').first()

    context = {
        'page_obj': page_obj,  # Cambiado de 'jobs' a 'page_obj'
        'search_query': search_query,
        'sectors': sectors,
        'countries': countries,
        'latest_entry': latest_entry

    }
    return render(request, 'login/index.html', context)


def get_user_type(user):
    if hasattr(user, 'userprofile'):
        return 'Usuario'
    elif hasattr(user, 'company'):
        return 'Empresa'
    elif user.is_staff or user.is_superuser:
        return 'Admin'
    else:
        return None



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
                phone_number=form.cleaned_data.get('phone_number'),
                bio=request.POST.get('bio'),
                genero=form.cleaned_data.get('genero'),
                document_type=form.cleaned_data.get('document_type'),
                document_number=form.cleaned_data.get('document_number'),
                # Agrega aquí la lógica para otros campos si es necesario
            )
            user_profile.save()
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login/signup_user.html', {'form': form})

def some_view(request):
    # Suponiendo que 'countries' es una lista de objetos de país que obtienes de tu modelo o forma estática
    countries = [
        {'country_code': 'AR', 'country_name': 'Argentina'},
        {'country_code': 'IT', 'country_name': 'Italia'},
        # Añade otros países si es necesario
    ]
    # ... resto de tu lógica de la vista ...
    return render(request, 'index.html', {'countries': countries})


def signup_comp(request):

    if request.user.is_authenticated:
        return redirect('/')

    # Tus otros caminos para cargar archivos JSON...
    sectors_json_path = finders.find('accounts/lista/sectores.json')
    provinces_json_path = finders.find('accounts/argentina/provincias.json')
    cities_json_path = finders.find('accounts/argentina/localidades.json')

    # Tus métodos para cargar datos estáticos...
    sector_choices, provinces, province_to_cities_map = load_static_data(
        sectors_json_path, provinces_json_path, cities_json_path
    )

    if request.method == 'POST':

        form = CompanySignUpForm(request.POST, request.FILES)
        form.fields['sector'].choices = sector_choices

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guarda el objeto User
                    user = form.save(commit=False)
                    user.save()
                    province_id = form.cleaned_data['province_name']
                    province_name = id_to_province_name(province_id)

                    # Aquí puedes agregar lógica adicional si necesitas crear un perfil de usuario
                    # ...

                    # Creamos el objeto Company asociado al usuario
                    company = Company(
                        user=user,
                        company_name=form.cleaned_data['company_name'],
                        contact_email=form.cleaned_data['email'],  # Asigna el email al contact_email de Company
                        phone_number=form.cleaned_data['phone_number'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        sector=form.cleaned_data['sector'],
                        razón_social=form.cleaned_data['razón_social'],
                        cantidad_empleados=form.cleaned_data['cantidad_empleados'],
                        cuit=form.cleaned_data['cuit'],
                        province_name=province_name,  # Asigna el nombre de la provincia

                        # Aquí deberías manejar los campos específicos de Italia si es el caso
                        # ...
                    )
                    company.country = form.cleaned_data.get('country')

                    # Manejo de los campos específicos de Italia y Argentina
                    country = form.cleaned_data.get('country')
                    if form.cleaned_data['country'] == 'IT':
                        company.region_it = form.cleaned_data.get('region_it', '')
                        company.provincia_it = form.cleaned_data.get('provincia_it', '')
                        company.comuna_it = form.cleaned_data.get('comuna_it', '')
                    else:
                        if 'province_name' in form.cleaned_data:
                            province_id = form.cleaned_data['province_name']
                            company.province_name = id_to_province_name(province_id)
                        else:
                            company.province_name = form.cleaned_data.get('province_name', '')
                            company.city = form.cleaned_data.get('city', '')

                    company.save()

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
        return redirect('/')

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si el usuario es un administrador
            if user.is_superuser or user.is_staff:
                messages.error(request, 'Los administradores deben iniciar sesión desde la página de administrador.')
                return redirect('signin')
            
            login(request, user)

            # Eliminar sesiones anteriores
            UserSession.objects.filter(user=user).delete()

            # Crear una nueva sesión de usuario
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                device_identifier=request.META.get('HTTP_USER_AGENT')
            )

            return redirect('/')
        else:
            messages.error(request, 'Acceso restringido o usuario/contraseña incorrecta')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login/signin.html', {'form': form})

def signin_view(request):
    form = CustomAuthenticationForm()
    # ... tu lógica para manejar el POST y autenticar al usuario ...
    return render(request, 'signin.html', {'form': form})

def signin_admin(request):
    if request.user.is_authenticated:
        return redirect('/')  # Ajusta esta ruta según sea necesario

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if user.is_superuser or user.is_staff:
                login(request, user)

                # Eliminar sesiones anteriores de este usuario
                UserSession.objects.filter(user=user).delete()

                # Crear una nueva entrada de UserSession para esta sesión
                UserSession.objects.create(
                    user=user,
                    session_key=request.session.session_key,
                    device_identifier=request.META.get('HTTP_USER_AGENT')
                )

                return redirect('/')  # Ajusta esta ruta según sea necesario
            else:
                messages.error(request, 'Acceso restringido a usuarios administradores.')

        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    else:
        form = AuthenticationForm()

    return render(request, 'login/signin_admin.html', {'form': form})


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
        job_post.expiration_date = form.cleaned_data['expiration_date']

        # Si el país seleccionado es Italia, procesa los campos de Italia
        if form.cleaned_data['country'] == 'IT':
            job_post.region_it = form.cleaned_data.get('region_it', '')
            job_post.provincia_it = form.cleaned_data.get('provincia_it', '')
            job_post.comuna_it = form.cleaned_data.get('comuna_it', '')
            # Puedes asignar None o un valor predeterminado a los campos de Argentina
            job_post.province_name =  ''
            job_post.city =  ''
        # Si no, procesa los campos de Argentina
        else:
            if 'province_name' in form.cleaned_data:
                province_id = form.cleaned_data['province_name']
                job_post.province_name = id_to_province_name(province_id)
            else:
                job_post.province_name = form.cleaned_data.get('province_name', '')
                job_post.city = form.cleaned_data.get('city', '')

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
            form.save()  # Esto debería guardar la imagen en el objeto userprofile
            messages.success(request, 'Imagen de perfil actualizada.')  # Mensaje de confirmación
            return redirect('my_profile')  # Redirige a la URL de perfil
    else:
        form = UserProfileForm(instance=request.user.userprofile)

    return render(request, 'profile/my_profile.html', {'form': form})


# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_superuser  # Cambia is_admin por is_superuser

@login_required
@user_passes_test(is_admin)
def admin_blog(request):
    entry = BlogEntry.objects.first() or BlogEntry()
    blog_form = BlogEntryForm(request.POST or None, instance=entry)
    faq_instance = FAQ.objects.first()  # Obtén la primera FAQ o None si no existe
    faq_form = FAQForm(request.POST or None, instance=faq_instance)
    question_instance = Question.objects.first()  # Obtén la primera FAQ o None si no existe
    question_form = QuestionForm(request.POST or None, instance=question_instance)
    
    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'save_blog' and blog_form.is_valid():
            blog_form.save()
            messages.success(request, 'La entrada del blog ha sido actualizada con éxito.')
            return redirect('/')  # Redirige a la ruta de inicio ('/')

        if 'action' in request.POST and request.POST['action'] == 'save_faq' and faq_form.is_valid():
            faq_form.save()
            messages.success(request, 'FAQ guardada con éxito.')
            return redirect('/faqs/')  # Redirige a la ruta de FAQs ('/faqs/')
        
        question_form = QuestionForm(request.POST or None)
        if request.method == 'POST':
            if 'action' in request.POST and request.POST['action'] == 'save_question':
                if question_form.is_valid():
                    question_form.save()
                    messages.success(request, 'Pregunta guardada con éxito.')
                    return redirect('/faqs/')
                else:
                    messages.error(request, 'Error en el formulario de pregunta.')

    # ... código existente ...
    context = {'blog_form': blog_form, 'faq_form': faq_form, 'question_form': question_form}
    return render(request, 'admin/admin_blog.html', context)

def faqs(request):
    faqs = FAQ.objects.all()
    questions = Question.objects.all()  # Agregamos esto

    return render(request, 'admin/faqs.html', {'faqs': faqs, 'questions': questions})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.delete()
    messages.success(request, 'La pregunta ha sido eliminada.')
    return redirect('faqs')


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

    # Inicializamos is_applied en False
    is_applied = False

    # Comprobamos si el usuario es una empresa o un usuario con perfil
    if hasattr(request.user, 'userprofile'):
        # Si el usuario es un perfil de usuario, comprobamos si ya se postuló al trabajo
        is_applied = Application.objects.filter(job=job, user_profile=request.user.userprofile).exists()
    elif hasattr(request.user, 'company'):
        # Aquí puedes agregar lógica adicional si quieres manejar algo específico para los usuarios de empresa
        pass

    # Pasamos is_applied y job al contexto de la plantilla
    context = {
        'job': job,
        'is_applied': is_applied
    }

    return render(request, 'jobs/job_details.html', context)






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
            job.sector = data.get('sector', job.sector)
            job.application_limit = data.get('application_limit', job.application_limit)

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
    
    if job.expiration_date < timezone.now().date():
        messages.error(request, 'La fecha de vencimiento para este trabajo ha pasado y no se aceptan más postulaciones.')
        return redirect('job_details', job_id=job_id)
    
    # Verificar si ya se ha alcanzado el límite de postulaciones
    if job.application_limit <= 0:
        messages.error(request, 'Este trabajo ya ha alcanzado el número máximo de postulaciones.')
        return redirect('job_details', job_id=job_id)

    user_profile = request.user.userprofile
    # Verificar si el usuario ya se ha postulado
    if Application.objects.filter(job=job, user_profile=user_profile).exists():
        messages.info(request, 'Ya te has postulado para este puesto.')
        return redirect('job_details', job_id=job_id)

    # Crear la postulación y actualizar el límite
    with transaction.atomic():
        job.refresh_from_db()
        if job.application_limit > 0:
            Application.objects.create(job=job, user_profile=user_profile)
            job.application_limit -= 1
            job.save()
            messages.success(request, 'Te has postulado exitosamente para este puesto.')
        else:
            messages.error(request, 'Este trabajo ya ha alcanzado el número máximo de postulaciones.')

    return redirect('job_details', job_id=job_id)


@login_required
def my_applications(request):
    user_profile = request.user.userprofile
    applications = Application.objects.filter(user_profile=user_profile).select_related('job')
    return render(request, 'jobs/my_applications.html', {'applications': applications})

@login_required
def view_applicants(request, job_id):
    job = get_object_or_404(JobPost, pk=job_id, company=request.user.company)
    applications = Application.objects.filter(job=job).select_related('user_profile')
    return render(request, 'jobs/view_applicants.html', {'job': job, 'applications': applications})
