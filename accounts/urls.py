from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import admin_blog

# Tus otras URLs...



urlpatterns = [
    path('', views.index, name='index'),  # Asegúrate de que 'views.index' es tu función de vista que maneja la búsqueda

    path('signup/', views.signup_user, name='signup_user'),
    path('signup_comp/', views.signup_comp, name='signup_comp'),
    path('signup_admin/', views.signup_admin, name='signup_admin'),
    path('signout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('signin_admin/', views.signin_admin, name='signin_admin'),
    path('manage_companies/', views.manage_companies, name='manage_companies'),
    path('company_details/<int:company_id>/', views.company_details, name='company_details'),
    path('activate_company/<int:company_id>/', views.activate_company, name='activate_company'),
    path('inactivate_company/<int:company_id>/', views.inactivate_company, name='inactivate_company'),
    path('create_job_post/', views.create_job_post, name='create_job_post'),
    path('my_job_list/', views.my_job_list, name='my_job_list'),
    path('delete_job_post/<int:job_id>/', views.delete_job_post, name='delete_job_post'),
    path('toggle_job_post_status/<int:job_id>/', views.toggle_job_post_status, name='toggle_job_post_status'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('upload-cv/', views.upload_cv, name='upload_cv'),
    path('admin_blog/', views.admin_blog, name='admin_blog'),
    path('faqs/', views.faqs, name='faqs'),
    path('ruta-para-actualizar-datos/', views.update_user_data, name='update_user_data'),
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('ruta-para-obtener-sectores/', views.load_sectors, name='load_sectors'),
    path('job_details/<int:job_id>/', views.job_details, name='job_details'),
    path('edit-job/<int:job_id>/', views.edit_job_post, name='edit_job_post'),
    path('apply_for_job/<int:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('my_applications/', views.my_applications, name='my_applications'),
    path('jobs/<int:job_id>/applicants/', views.view_applicants, name='view_applicants'),
    path('questions/delete/<int:question_id>/', views.delete_question, name='delete_question'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)