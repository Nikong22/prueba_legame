from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('signup/', views.signup_user, name='signup_user'),
    path('signup_comp/', views.signup_comp, name='signup_comp'),
    path('signup_admin/', views.signup_admin, name='signup_admin'),
    path('signout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    

    ]