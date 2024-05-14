from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('podcast/<int:podcast_id>', views.get_podcast_details, name='get_podcast_details')
]
