# Create your views here.
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import uuid
from datetime import timedelta


def subscribe(request):

    if not request.session.get('user_email'):
        return redirect('login')
    
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


def riwayat(request):
 
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']
    print(email)

    # Execute a raw SQL query to retrieve transactions for the logged-in user
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.transaction WHERE email = %s", [email])
        user_transactions = cursor.fetchall()

    # Pass the transactions to the template
    context = {
        'transactions': user_transactions
    }

    return render(request, 'riwayat.html', context)

import logging
from django.db import connection, DatabaseError
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
import uuid

# Set up logging
logger = logging.getLogger(__name__)

def pembayaran_view(request):
    if request.method == 'POST':
        user_email = request.session.get('user_email')
        if not user_email:
            return redirect('login')

        jenis_paket = request.GET.get('jenis', '')
        harga = request.GET.get('harga', '')
        metode_bayar = request.POST.get('metode_bayar')

        timestamp_dimulai = timezone.now()
        if jenis_paket == '1 Bulan':
            timestamp_berakhir = timestamp_dimulai + timedelta(days=30)
        elif jenis_paket == '3 Bulan':
            timestamp_berakhir = timestamp_dimulai + timedelta(days=90)
        elif jenis_paket == '6 Bulan':
            timestamp_berakhir = timestamp_dimulai + timedelta(days=180)
        else:
            timestamp_berakhir = timestamp_dimulai + timedelta(days=365)

        try:
            with connection.cursor() as cursor:
                # Insert into Premium table
                cursor.execute("""
                    INSERT INTO marmut.premium (email)
                    VALUES (%s)
                    ON CONFLICT (email) DO NOTHING
                """, [user_email])

                # Remove from NonPremium table
                cursor.execute("""
                    DELETE FROM marmut.non_premium WHERE email = %s
                """, [user_email])

                # Insert into Transaction table
                transaction_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO marmut.transaction (id, jenis_paket, email, timestamp_dimulai, timestamp_berakhir, metode_bayar, nominal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [transaction_id, jenis_paket, user_email, timestamp_dimulai, timestamp_berakhir, metode_bayar, harga])

            return redirect('success_page')

        except DatabaseError as e:
            logger.error("Database error occurred: %s", e)
            return render(request, 'pembayaran.html', {'jenis': jenis_paket, 'harga': harga, 'error': str(e)})

    jenis = request.GET.get('jenis', '')
    harga = request.GET.get('harga', '')
    return render(request, 'pembayaran.html', {'jenis': jenis, 'harga': harga})

def downloaded_songs(request):
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']
    print(email)

    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT ds.id_song, m.judul, c.nama
            FROM marmut.downloaded_song AS ds
            INNER JOIN marmut.konten AS m ON ds.id_song = m.id
            INNER JOIN marmut.akun AS c ON ds.email_downloader = c.email
            WHERE ds.email_downloader = %s
        """, [email])
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

def delete_song(request, song_id):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM marmut.downloaded_song WHERE id_song = %s", [song_id])
        return redirect('marmut:downloadedsongs')
    return redirect('marmut:downloadedsongs')

##delete done, add prem, remove non prem
##belum bisa add transaction
