# Create your views here.
from django.shortcuts import render
from django.db import connection
from django.contrib.auth.decorators import login_required

def subscribe(request):
    # Raw query to fetch subscription packages from the database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT jenis, harga
            FROM marmut.paket
        """)
        packages = cursor.fetchall()

    # Prepare data to be passed to the template
    context = {
        'packages': packages,
    }

    return render(request, 'subscribe.html', context)

def pembayaran_view(request):
    jenis = request.GET.get('jenis', '')
    harga = request.GET.get('harga', '')

    # Perform any necessary processing with jenis and harga here

    return render(request, 'pembayaran.html', {'jenis': jenis, 'harga': harga})

def downloaded_songs(request):
    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT ds.id_song, m.judul, c.nama
            FROM marmut.downloaded_song AS ds
            INNER JOIN marmut.konten AS m ON ds.id_song = m.id
            INNER JOIN marmut.akun AS c ON ds.email_downloader = c.email
        """)
        downloaded_songs_data = cursor.fetchall()

    return render(request, 'downloadedsong.html', {'downloaded_songs': downloaded_songs_data})

def search_find(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, judul, tanggal_rilis, tahun, durasi
                FROM marmut.konten
                WHERE judul ILIKE %s
            """, [f'%{query}%'])
            results = cursor.fetchall()

    context = {
        'query': query,
        'results': results
    }
    return render(request, 'searchfind.html', context)
