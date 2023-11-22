from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import admin_blog

# Tus otras URLs...



urlpatterns = [
    path('', views.login_view, name='login_view'),
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

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)