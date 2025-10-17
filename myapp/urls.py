from django.urls import path
from . import views #impporta todas las funciones

urlpatterns = [
    path('', views.welcome,name='welcome'),
    path('login/', views.login_view,name='login'),
    path('register/',views.register, name='register'),
    path('verify_code/', views.verify_code, name='verify_code'),
    path('forgot_password/',views.forgot_password, name='forgot_password'),
    path('verify_reset_code/',views.verify_reset_code, name='verify_reset_code'),
    path('reset_password/',views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name="logout"),
    path('home/', views.home, name='home'),
    path('historia_clinica/', views.historia_clinica, name='historia_clinica'),
    path('prediccion/', views.hacer_prediccion_view, name='hacer_prediccion'),
]