from django.urls import path, include
from . import views

app_name = 'marmut'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('pembayaran/', views.pembayaran_view, name='pembayaran'),
    path('downloadedsongs/', views.downloaded_songs, name='downloadedsongs'),
    path('downloadedsong/', views.downloaded_songs, name='downloadedsongs'),
    path('searchfind/', views.search_find, name='searchfind'),
    path('riwayat/', views.riwayat, name='riwayat'),
    path('deletesong/<uuid:song_id>/', views.delete_song, name='delete_song'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('register_user/', views.register_user, name='register_user'),  
    path('register_label/', views.register_label, name='register_label')
]
