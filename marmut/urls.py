from django.urls import path
from . import views

app_name = 'marmut'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('pembayaran/', views.pembayaran_view, name='pembayaran'),
    path('downloadedsongs/', views.downloaded_songs, name='downloadedsongs'),
    path('downloadedsong/', views.downloaded_songs, name='downloadedsongs'),
    path('searchfind/', views.search_find, name='searchfind'),

]
