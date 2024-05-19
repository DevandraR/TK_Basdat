from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError, connection, transaction, DatabaseError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import uuid
from datetime import timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

def subscribe(request):
    if not request.session.get('user_email'):
        return redirect('login')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT jenis, harga
            FROM marmut.paket
        """)
        packages = cursor.fetchall()

    context = {
        'packages': packages,
    }

    return render(request, 'subscribe.html', context)

def riwayat(request):
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']
    print(email)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.transaction WHERE email = %s", [email])
        user_transactions = cursor.fetchall()

    context = {
        'transactions': user_transactions
    }

    return render(request, 'riwayat.html', context)

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
                cursor.execute("""
                    INSERT INTO marmut.premium (email)
                    VALUES (%s)
                    ON CONFLICT (email) DO NOTHING
                """, [user_email])

                cursor.execute("""
                    DELETE FROM marmut.non_premium WHERE email = %s
                """, [user_email])

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

def determine_user_type(email, cursor):
    user_type = {
        'is_podcaster': False,
        'is_artist': False,
        'is_songwriter': False,
        'is_label': False,
        'is_non_premium': False,
        'is_premium': False,
    }

    cursor.execute("SELECT 1 FROM marmut.podcaster WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_podcaster'] = True

    cursor.execute("SELECT 1 FROM marmut.artist WHERE email_akun = %s", [email])
    if cursor.fetchone():
        user_type['is_artist'] = True

    cursor.execute("SELECT 1 FROM marmut.label WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_label'] = True

    cursor.execute("SELECT 1 FROM marmut.non_premium WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_non_premium'] = True

    cursor.execute("SELECT 1 FROM marmut.premium WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_premium'] = True

    return user_type

def dashboard(request):
    email = request.session.get('user_email')
    if email is None:
        return redirect('login')

    with connection.cursor() as cursor:
        user_type = determine_user_type(email, cursor)

        cursor.execute("SELECT * FROM marmut.akun WHERE email = %s", [email])
        user_profile = cursor.fetchone()

        roles = []
        if user_type['is_podcaster']:
            roles.append('Podcaster')
        if user_type['is_artist']:
            roles.append('Artist')
        if user_type['is_songwriter']:
            roles.append('Songwriter')
        if user_type['is_label']:
            roles.append('Label')
        if user_type['is_non_premium']:
            roles.append('Non-Premium')
        if user_type['is_premium']:
            roles.append('Premium')
        
        user_profile_roles = ', '.join(roles)

        user_data = {}
        if user_type['is_premium'] or user_type['is_non_premium']:
            cursor.execute("SELECT judul FROM marmut.user_playlist WHERE email_pembuat = %s", [email])
            user_data['playlists'] = [playlist[0] for playlist in cursor.fetchall()]
        if user_type['is_artist'] or user_type['is_songwriter']:
            cursor.execute("SELECT judul FROM marmut.konten JOIN marmut.song ON marmut.konten.id = marmut.song.id_konten WHERE id_artist = %s", [email])
            user_data['songs'] = [song[0] for song in cursor.fetchall()]
        if user_type['is_podcaster']:
            cursor.execute("SELECT judul FROM marmut.konten JOIN marmut.podcast ON marmut.konten.id = marmut.podcast.id_konten WHERE email_podcaster = %s", [email])
            user_data['podcasts'] = [podcast[0] for podcast in cursor.fetchall()]
        if user_type['is_label']:
            cursor.execute("SELECT judul FROM marmut.album WHERE id_label = %s", [email])
            user_data['albums'] = [album[0] for album in cursor.fetchall()]

    return render(request, 'dashboard.html', {'user_profile': user_profile, 'user_data': user_data, 'user_type': user_type, 'user_profile_roles': user_profile_roles})

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM marmut.akun WHERE email = %s AND password = %s", [email, password])
            user = cursor.fetchone()

            if user is None:
                cursor.execute("SELECT * FROM marmut.label WHERE email = %s AND password = %s", [email, password])
                user = cursor.fetchone()
                request.session['label_email'] = email

            if user is not None:
                request.session['user_email'] = str(user[0])
                request.session['user_type'] = determine_user_type(email, cursor)
                return redirect('dashboard')
            else:
                messages.error(request, 'Email or password is incorrect!')
                return redirect('login')
    else:
        return render(request, 'login.html')

def homepage(request):
    user_email = request.session.get('user_email')

    if user_email is not None:
        with connection.cursor() as cursor:
            user_type = determine_user_type(user_email, cursor)
        return render(request, 'homepage.html', {'user_email': user_email, 'user_type': user_type})
    else:
        return render(request, 'homepage.html', {'user_email': user_email})

def register(request):
    return render(request, 'register.html')

def register_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        name = request.POST['name']
        gender = request.POST['gender']
        birthplace = request.POST['birthplace']
        birthdate = request.POST['birthdate']
        city = request.POST['city']
        role = request.POST.getlist('role')

        gender = 1 if gender == 'Male' else 0

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM marmut.akun WHERE email = %s", [email])
            user = cursor.fetchone()

            if user is not None:
                messages.error(request, 'Email already exists!')
                return render(request, 'register.html')

            try:
                with transaction.atomic():
                    cursor.execute("""
                        INSERT INTO marmut.akun (email, password, nama, gender, tempat_lahir, tanggal_lahir, is_verified, kota_asal) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [email, password, name, gender, birthplace, birthdate, len(role) > 0, city])

                    for r in role:
                        if r == 'Podcaster':
                            cursor.execute("INSERT INTO marmut.podcaster (email) VALUES (%s)", [email])
                        elif r == 'Artist':
                            id_pemilik_hak_cipta_artist = uuid.uuid4()
                            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta_artist, 0])
                            cursor.execute("INSERT INTO marmut.artist (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [uuid.uuid4(), email, id_pemilik_hak_cipta_artist])
                        elif r == 'Songwriter':
                            id_pemilik_hak_cipta_songwriter = uuid.uuid4()
                            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta_songwriter, 0])
                            cursor.execute("INSERT INTO marmut.songwriter (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [uuid.uuid4(), email, id_pemilik_hak_cipta_songwriter])

                    if len(role) == 0:
                        cursor.execute("INSERT INTO marmut.non_premium (email) VALUES (%s)", [email])

                messages.success(request, 'Registration successful!')
                return render(request, 'register.html')

            except IntegrityError as e:
                messages.error(request, f'An error occurred during registration: {e}')
                return render(request, 'register.html')

    else:
        return redirect('register')

def register_label(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        name = request.POST['name']
        contact = request.POST['contact']

        if not email or not password or not name or not contact:
            messages.error(request, 'All fields are required!')
            return redirect('register')

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM marmut.akun WHERE email = %s UNION SELECT email FROM marmut.label WHERE email = %s", [email, email])
            user = cursor.fetchone()

            if user is not None:
                messages.error(request, 'Email already exists!')
                return redirect('register')

            id = uuid.uuid4()
            id_pemilik_hak_cipta = uuid.uuid4()

            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta, 0])

            cursor.execute("INSERT INTO marmut.label (id, email, password, nama, kontak, id_pemilik_hak_cipta) VALUES (%s, %s, %s, %s, %s, %s)", [id, email, password, name, contact, id_pemilik_hak_cipta])

            messages.success(request, 'Registration successful!')
            return redirect('login')

    else:
        return redirect('register')

def logout(request):
    try:
        del request.session['user_email']
    except KeyError:
        pass
    return redirect('homepage')
