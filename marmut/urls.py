from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('register_user/', views.register_user, name='register_user'),  
    path('register_label/', views.register_label, name='register_label')
]
