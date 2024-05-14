from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. This is your app.")

def get_podcast_details(request, podcast_id):
    with connection.cursor() as cursor:
        # Fetch podcast details
        cursor.execute("""
            SELECT K.judul, array_agg(G.genre), A.nama, K.durasi, K.tanggal_rilis, K.tahun
            FROM KONTEN K
            JOIN PODCAST P ON K.id = P.id_konten
            JOIN PODCASTER Po ON P.email_podcaster = Po.email
            JOIN AKUN A ON Po.email = A.email
            JOIN GENRE G ON K.id = G.id_konten
            WHERE K.id = %s
            GROUP BY K.judul, A.nama, K.durasi, K.tanggal_rilis, K.tahun
        """, [podcast_id])

        podcast = cursor.fetchone()

        # Fetch podcast episodes
        cursor.execute("""
            SELECT E.judul, E.deskripsi, E.durasi, E.tanggal_rilis
            FROM EPISODE E
            WHERE E.id_konten_podcast = %s
            ORDER BY E.tanggal_rilis DESC
        """, [podcast_id])

        episodes = cursor.fetchall()

    return render(request, 'marmut/playPodcast.html', {'podcast': podcast, 'episodes': episodes})