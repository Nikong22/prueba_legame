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
from .models import JobPost, BlogEntry, Application, BlogEntryTranslation
from django.contrib.staticfiles import finders
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import UserSession  # Asegúrate de importar UserSession
from .forms import CustomAuthenticationForm, AdminCreationForm
from django.db.models import Count
from django.core.paginator import Paginator
from .models import FAQ, Question, FAQTranslation
from .forms import FAQForm, QuestionForm
from django.core.signing import Signer, BadSignature
from django.core.mail import send_mail
from django.urls import reverse
from .utils import id_to_province_name
import os
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.encoding import force_bytes
from django.http import HttpResponseRedirect
from .email_utils import send_verification_email  # Asegúrate de importar send_verification_email
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from .models import Question, QuestionTranslation
from .forms import QuestionForm




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
        form = CustomUserCreationForm(request.POST, request=request)
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
            return render(request, 'email/registration_success.html')
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

        form = CompanySignUpForm( request.POST, request=request)
        form.fields['sector'].choices = sector_choices

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guarda el objeto User
                    user = form.save()
                    #user.save()
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
                    # try:
                    #     print("Antes de llamar a send_verification_email")
                    #     send_verification_email(user, request)
                    #     print("Después de llamar a send_verification_email")
                    #     #logger.info("Correo de verificación enviado correctamente.")
                    # except Exception as e:
                    #     print(f"Excepción capturada en send_verification_email: {e}")
                    #     #logger.error(f"Error al enviar correo de verificación: {e}")

                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return render(request, 'email/registration_success.html')
            except IntegrityError as e:
                messages.error(request, f'Hubo un error al crear la cuenta: {e}')
            finally:
                try:
                    print("Antes de llamar a send_verification_email")
                    send_verification_email(user, request)
                    print("Después de llamar a send_verification_email")
                    #logger.info("Correo de verificación enviado correctamente.")
                except Exception as e:
                    print(f"Excepción capturada en send_verification_email: {e}")
                    #logger.error(f"Error al enviar correo de verificación: {e}")
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
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user, request)  # Aquí se pasa el 'request'
            return render(request, 'email/registration_success.html')
    else:
        form = AdminCreationForm()

    return render(request, 'login/signup_admin.html', {'form': form})






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
            
            
            # Verificar si el correo electrónico ha sido confirmado
            if hasattr(user, 'userprofile') and not user.userprofile.email_confirmed:
                messages.error(request, 'Por favor, activa tu cuenta desde el enlace enviado a tu email.')
                return render(request, 'login/signin.html', {'form': form})
            elif hasattr(user, 'company') and not user.company.email_confirmed:
                messages.error(request, 'Por favor, activa tu cuenta desde el enlace enviado a tu email.')
                return render(request, 'login/signin.html', {'form': form})
            
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
            messages.error(request, _('ERROR_LOGIN'))
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
                  # Verificar si el correo electrónico del administrador ha sido confirmado
                if hasattr(user, 'adminuser') and not user.adminuser.email_confirmed:
                    messages.error(request, 'Por favor, activa tu cuenta desde el enlace enviado a tu email.')
                    return render(request, 'login/signin_admin.html', {'form': form})

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
    entry = BlogEntry.objects.first()  # Asume que siempre hay al menos una entrada
    entry_es = entry.get_translation('es') if entry else None
    entry_it = entry.get_translation('it') if entry else None
    if not entry:
        entry = BlogEntry.objects.create()

    if request.method == 'POST':
        if 'save_blog_es' in request.POST:
            blog_form_es = BlogEntryForm(request.POST, instance=entry, prefix='es')
            if blog_form_es.is_valid():
                blog_entry = blog_form_es.save(commit=False)
                blog_entry.save()
                BlogEntryTranslation.objects.update_or_create(
                    blog_entry=blog_entry, language='es',
                    defaults={
                        'title': blog_form_es.cleaned_data.get('title'),
                        'content': blog_form_es.cleaned_data.get('content')
                    }
                )
                messages.success(request, 'La entrada del blog en español ha sido actualizada con éxito.')
                return redirect('admin_blog')

        elif 'save_blog_it' in request.POST:
            blog_form_it = BlogEntryForm(request.POST, instance=entry, prefix='it')
            if blog_form_it.is_valid():
                blog_entry = blog_form_it.save(commit=False)
                blog_entry.save()
                BlogEntryTranslation.objects.update_or_create(
                    blog_entry=blog_entry, language='it',
                    defaults={
                        'title': blog_form_it.cleaned_data.get('title'),
                        'content': blog_form_it.cleaned_data.get('content')
                    }
                )
                messages.success(request, 'La entrada del blog en italiano ha sido actualizada con éxito.')
                return redirect('admin_blog')

    # Si no es POST o si es un GET, se cargan los formularios con los datos existentes
    blog_form_es = BlogEntryForm(instance=entry_es, prefix='es') if entry_es else BlogEntryForm(prefix='es')
    blog_form_it = BlogEntryForm(instance=entry_it, prefix='it') if entry_it else BlogEntryForm(prefix='it')


    context = {
        'blog_form_es': blog_form_es,
        'blog_form_it': blog_form_it,
        'entry_es': entry_es,
        'entry_it': entry_it,
    }
    return render(request, 'admin/admin_blog.html', context)

def save_blog_in_language(request, form, language_code):
    blog_entry = form.save(commit=False)
    blog_entry.save()
    BlogEntryTranslation.objects.update_or_create(
        blog_entry=blog_entry, language=language_code,
        defaults={
            'title': form.cleaned_data[f'title_{language_code}'],
            'content': form.cleaned_data[f'content_{language_code}']
        }
    )
    messages.success(request, f'La entrada del blog en {language_code} ha sido actualizada con éxito.')
    return redirect('/')

def faqs(request):
    language_code = get_language()  # Obtienes el código de idioma actual de la sesión
    faqs_translated = FAQ.objects.all().prefetch_related('translations')

    # Agregas las traducciones al contexto
    context = {'faqs': faqs_translated, 'language_code': language_code}
    return render(request, 'admin/faqs.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_faq(request):
    print("Accediendo a la vista admin_faq")

    # Obtener instancias de FAQTranslation
    faq_es_instance = FAQTranslation.objects.filter(language='es').first()
    faq_it_instance = FAQTranslation.objects.filter(language='it').first()

    # Estableceremos un ID único o título para las FAQs que serán constantes y conocidos.
    FAQ_ID = 1  # Reemplazar con el ID real o mecanismo de identificación que estés utilizando

    # Crear instancias de formularios con datos iniciales
    form_es_initial = {'title_es': faq_es_instance.title, 'content_es': faq_es_instance.content} if faq_es_instance else {}
    form_it_initial = {'title_it': faq_it_instance.title, 'content_it': faq_it_instance.content} if faq_it_instance else {}

    form_es = FAQForm(prefix='es', initial=form_es_initial)
    form_it = FAQForm(prefix='it', initial=form_it_initial)

    if request.method == 'POST':
        print("Método POST detectado")

        title_es = request.POST.get('title_es', '').strip()
        content_es = request.POST.get('content_es', '').strip()
        title_it = request.POST.get('title_it', '').strip()
        content_it = request.POST.get('content_it', '').strip()

        if 'save_faq_es' in request.POST:
            print("Botón para guardar FAQ en español presionado")
            form_es = FAQForm(prefix='es', data=request.POST, initial=form_es_initial)
            form_it = FAQForm(prefix='it', initial=form_it_initial)  # Creamos una instancia de formulario italiano vacía
            if form_es.is_valid():
                faq_instance, _ = FAQ.objects.get_or_create(id=FAQ_ID, defaults={'title': title_es})
                faq_translation, _ = FAQTranslation.objects.update_or_create(
                    faq=faq_instance,
                    language='es',
                    defaults={
                        'title': title_es,
                        'content': content_es
                    }
                )
                print(f"FAQ en español actualizada: {faq_translation}")
                messages.success(request, 'La FAQ en español ha sido actualizada con éxito.')
            else:
                messages.error(request, 'Error al validar el formulario en español.')

        elif 'save_faq_it' in request.POST:
            print("Botón para guardar FAQ en italiano presionado")
            form_it = FAQForm(prefix='it', data=request.POST, initial=form_it_initial)
            form_es = FAQForm(prefix='es', initial=form_es_initial)  # Creamos una instancia de formulario español vacía
            if form_it.is_valid():
                faq_instance, _ = FAQ.objects.get_or_create(id=FAQ_ID, defaults={'title': title_it})
                faq_translation, _ = FAQTranslation.objects.update_or_create(
                    faq=faq_instance,
                    language='it',
                    defaults={
                        'title': title_it,
                        'content': content_it
                    }
                )
                print(f"FAQ en italiano actualizada: {faq_translation}")
                messages.success(request, 'La FAQ en italiano ha sido actualizada con éxito.')
            else:
                messages.error(request, 'Error al validar el formulario en italiano.')

        return redirect('faqs')

    context = {
        'form_es': form_es,
        'form_it': form_it,
        'faq_es': faq_es_instance,
        'faq_it': faq_it_instance,
    }

    return render(request, 'admin/admin_faq.html', context)


def save_faq_in_language(request, form, language_code):
    blog_faq = form.save(commit=False)
    blog_faq.save()
    FAQTranslation.objects.update_or_create(
        blog_faq=blog_faq, language=language_code,
        defaults={
            'title': form.cleaned_data[f'title_{language_code}'],
            'content': form.cleaned_data[f'content_{language_code}']
        }
    )
    messages.success(request, f'La entrada del blog en {language_code} ha sido actualizada con éxito.')
    return redirect('/')


# views.py
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_questions(request):
    # Asumo que siempre habrá al menos una pregunta, ajusta según tus necesidades
    question = Question.objects.first()

    # Crear instancias de formularios para ESP e IT
    question_form_es = QuestionForm(prefix='es', instance=question)
    question_form_it = QuestionForm(prefix='it', instance=question)

    if request.method == 'POST':
        # Verificar qué botón se presionó
        if 'save_question_es' in request.POST:
            question_form_es = QuestionForm(request.POST, prefix='es', instance=question)
            language_code = 'es'
        elif 'save_question_it' in request.POST:
            question_form_it = QuestionForm(request.POST, prefix='it', instance=question)
            language_code = 'it'
        else:
            messages.error(request, 'Acción no válida.')
            return redirect('admin_questions')

        if question_form_es.is_valid() and question_form_it.is_valid():
            # Guardar la pregunta en el modelo base
            question_entry = question_form_es.save(commit=False)
            question_entry.save()

            # Actualizar las traducciones según el idioma seleccionado
            question_entry.title_es = question_form_es.cleaned_data.get('title_es')
            question_entry.short_answer_es = question_form_es.cleaned_data.get('short_answer_es')
            question_entry.complete_answer_es = question_form_es.cleaned_data.get('complete_answer_es')

            question_entry.title_it = question_form_it.cleaned_data.get('title_it')
            question_entry.short_answer_it = question_form_it.cleaned_data.get('short_answer_it')
            question_entry.complete_answer_it = question_form_it.cleaned_data.get('complete_answer_it')

            question_entry.save()
            
            messages.success(request, f'La pregunta ha sido actualizada con éxito en {language_code}.')
            
            # Redireccionar a la página correcta (puede ser 'admin_blog' o 'faqs' según tus necesidades)
            return redirect('admin_blog')

    context = {
        'question_form_es': question_form_es,
        'question_form_it': question_form_it,
        'question': question,
    }

    return render(request, 'admin/admin_questions.html', context)
def save_questions_in_language(request, form, language_code):
    question_entry = form.save(commit=False)
    question_entry.save()

    QuestionTranslation.objects.update_or_create(
        question=question_entry, language=language_code,
        defaults={
            'title': form.cleaned_data[f'title_{language_code}'],
            'short_answer': form.cleaned_data[f'short_answer_{language_code}'],
            'complete_answer': form.cleaned_data[f'complete_answer_{language_code}']
        }
    )

    messages.success(request, f'La pregunta en {language_code} ha sido actualizada con éxito.')
    return redirect('/')


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
    
    # Verifica si la fecha de vencimiento ha pasado o si se ha alcanzado el límite de postulaciones
    if job.expiration_date < timezone.now().date():
        messages.error(request, 'La fecha de vencimiento para este trabajo ha pasado y no se aceptan más postulaciones.')
        return redirect('job_details', job_id=job_id)
    
    if job.application_limit <= 0:
        messages.error(request, 'Este trabajo ya ha alcanzado el número máximo de postulaciones.')
        return redirect('job_details', job_id=job_id)

    user_profile = request.user.userprofile
    # Verifica si el usuario ya se ha postulado
    if Application.objects.filter(job=job, user_profile=user_profile).exists():
        messages.info(request, 'Ya te has postulado para este puesto.')
    else:
        with transaction.atomic():
            job.refresh_from_db()
            if job.application_limit > 0:
                application = Application.objects.create(job=job, user_profile=user_profile)
                job.application_limit -= 1
                job.save()

                # Envía el correo electrónico al usuario de la empresa
                subject = 'Nueva postulación para tu publicación de trabajo'
                message = render_to_string('new_application_notification.txt', {
                    'company': job.company,
                    'job': job,
                    'user_profile': user_profile,
                    'application': application,
                    'link_to_job': request.build_absolute_uri(reverse('view_applicants', args=[job.id]))
                })
                send_mail(
                    subject,
                    message,
                    'info@progettolegame.com',  # Correo electrónico del remitente
                    [job.company.contact_email],  # Correo electrónico del destinatario
                    fail_silently=False,
                )

                messages.success(request, 'Te has postulado exitosamente para este puesto.')

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





def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if hasattr(user, 'userprofile'):
            user.userprofile.email_confirmed = True
            user.userprofile.save()
            login(request, user)  # Inicia sesión automáticamente al usuario
            return redirect('activation_valid')
        elif hasattr(user, 'company'):
            user.company.email_confirmed = True
            user.company.save()
            login(request, user)  # Inicia sesión automáticamente al usuario
            return redirect('activation_valid')
        elif hasattr(user, 'adminuser'):
            user.adminuser.email_confirmed = True
            user.adminuser.save()
            # No inicia sesión automáticamente al administrador aquí
            return redirect('activation_valid_admin')  # Redirige a la página de inicio de sesión de admin
        else:
            return render(request, 'email/activation_invalid.html')
    else:
        return render(request, 'email/activation_invalid.html', {'uidb64': uidb64})

    
def activation_valid(request):
    is_admin = request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)
    context = {'is_admin': is_admin}
    return render(request, 'email/activation_valid.html', context)

def activation_valid_admin(request):
    is_admin = request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)
    context = {'is_admin': is_admin}
    return render(request, 'email/activation_valid_admin.html', context)



def resend_activation_email(request, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None:
        # token = default_token_generator.make_token(user)
        # activation_link = request.build_absolute_uri(
        #     reverse('activate_account', args=[urlsafe_base64_encode(force_bytes(user.pk)), token])
        # )
        # subject = 'Activación de Cuenta'
        # message = render_to_string('activation_email.txt', {
        #     'user': user,
        #     'url': activation_link,
        # })
        # send_mail(subject, message, 'nikongg22@gmail.com', [user.email], fail_silently=False)
        try:
            print("Antes de llamar a send_verification_email")
            send_verification_email(user, request)
            print("Después de llamar a send_verification_email")
            #logger.info("Correo de verificación enviado correctamente.")
        except Exception as e:
            print(f"Excepción capturada en send_verification_email: {e}")
            #logger.error(f"Error al enviar correo de verificación: {e}")
        # Redirige al usuario a la página de inicio de sesión después de reenviar el correo electrónico
        return redirect('/signin')
    else:
        # Si el uidb64 no es válido, puedes renderizar una plantilla de error o redirigir a otra página
        return render(request, '/')


