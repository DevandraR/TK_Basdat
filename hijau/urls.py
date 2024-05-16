from django.urls import path
from . import views

urlpatterns = [
    path('playlist/', views.playlist, name='playlist'),
    path('addplaylist/', views.add_playlist, name='addplaylist'),
]
