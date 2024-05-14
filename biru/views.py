from django.shortcuts import render
from django.db import connection

# Create your views here.
def get_podcast_details(request, podcast_id):
    with connection.cursor() as cursor:
        # Fetch podcast details
        cursor.execute("""
            SELECT K.judul, array_agg(G.genre), A.nama, K.durasi, K.tanggal_rilis, K.tahun
            FROM marmut.KONTEN K
            JOIN marmut.PODCAST P ON K.id = P.id_konten
            JOIN marmut.PODCASTER Po ON P.email_podcaster = Po.email
            JOIN marmut.AKUN A ON Po.email = A.email
            JOIN marmut.GENRE G ON K.id = G.id_konten
            WHERE K.id = %s
            GROUP BY K.judul, A.nama, K.durasi, K.tanggal_rilis, K.tahun
        """, [str(podcast_id)])

        podcast = cursor.fetchone()
        print(podcast)

        # Fetch podcast episodes
        cursor.execute("""
            SELECT E.judul, E.deskripsi, E.durasi, E.tanggal_rilis
            FROM marmut.EPISODE E
            WHERE E.id_konten_podcast = %s
            ORDER BY E.tanggal_rilis DESC
        """, [str(podcast_id)])

        episodes = cursor.fetchall()
        print(episodes)

    return render(request, 'playPodcast.html', {'podcast': podcast, 'episodes': episodes})