from django.urls import path
from . import views

urlpatterns = [
    path('playlist/', views.playlist, name='playlist'),
    path('playlist/<uuid:id_user_playlist>/', views.detail_playlist, name='detail_playlist'),
    path('playlist/<uuid:id_user_playlist>/change/', views.change_playlist, name='change_playlist'),
    path('playlist/<uuid:id_user_playlist>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlist/<uuid:id_user_playlist>/addsong/', views.add_song, name='addsong'),
    path('playlist/<str:id_user_playlist>/shuffle_play/', views.shuffle_play, name='shuffle_play'),
    path('addplaylist/', views.add_playlist, name='addplaylist'),
    path('song/<uuid:id_song>/', views.song_detail, name='song_detail'),
    path('song/<uuid:id_song>/play/', views.play_song, name='play_song'),
    path('song/<uuid:id_song>/download/', views.download_song, name='download_song'),
]