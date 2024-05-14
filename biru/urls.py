from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:podcast_id>/', views.get_podcast_details, name='get_podcast_details')
]