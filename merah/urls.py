from django.urls import path
from merah.views import cek_royalti, create_album, delete_album, kelola_album_and_song, list_album, album_detail, create_lagu, album_and_song

app_name = 'merah'

urlpatterns = [
    path('cek-royalti/', cek_royalti, name='cek_royalti'),
    path('kelola-album/', kelola_album_and_song, name='kelola_album_and_song'),
    path('list-album/', list_album, name='list_album'),
    path('album-detail/<str:album_id>/', album_detail, name='album_detail'),
    path('create-lagu/', create_lagu, name='create_lagu'),
    path('album-and-song/', album_and_song, name='album_and_song'),
    path('create-album', create_album, name='create-album'),
    path('delete-album/<str:album_id>', delete_album, name='delete_album'),
]