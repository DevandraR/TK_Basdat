from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError, connection, transaction
import uuid

def determine_user_type(email, cursor):
    user_type = {
        'is_podcaster': False,
        'is_artist': False,
        'is_songwriter': False,
        'is_label': False,
        'is_non_premium': False,
        'is_premium': False,
    }

    # Check if user is a podcaster
    cursor.execute("SELECT 1 FROM marmut.podcaster WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_podcaster'] = True

    # Check if user is an artist
    cursor.execute("SELECT 1 FROM marmut.artist WHERE email_akun = %s", [email])
    if cursor.fetchone():
        user_type['is_artist'] = True

    # Check if user is a label
    cursor.execute("SELECT 1 FROM marmut.label WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_label'] = True

    # Check if user is non-premium
    cursor.execute("SELECT 1 FROM marmut.non_premium WHERE email = %s", [email])
    if cursor.fetchone():
        user_type['is_non_premium'] = True

    # Check if user is premium
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

        # Fetch user profile
        cursor.execute("SELECT * FROM marmut.akun WHERE email = %s", [email])
        user_profile = cursor.fetchone()

        # Determine the roles
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

        # Fetch user-specific data
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
            # Check the 'akun' table
            cursor.execute("SELECT * FROM marmut.akun WHERE email = %s AND password = %s", [email, password])
            user = cursor.fetchone()

            # If not found in 'akun', check the 'label' table
            if user is None:
                cursor.execute("SELECT * FROM marmut.label WHERE email = %s AND password = %s", [email, password])
                user = cursor.fetchone()
                request.session['label_email'] = email

            if user is not None:
                # Convert the UUID to a string before storing it in the session
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

        # Convert gender to integer
        gender = 1 if gender == 'Male' else 0

        with connection.cursor() as cursor:
            # Check if email already exists
            cursor.execute("SELECT email FROM marmut.akun WHERE email = %s", [email])
            user = cursor.fetchone()

            if user is not None:
                messages.error(request, 'Email already exists!')
                return render(request, 'register.html')

            try:
                with transaction.atomic():
                    # Insert into akun table
                    cursor.execute("""
                        INSERT INTO marmut.akun (email, password, nama, gender, tempat_lahir, tanggal_lahir, is_verified, kota_asal) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [email, password, name, gender, birthplace, birthdate, len(role) > 0, city])

                    # Insert into role table
                    for r in role:
                        if r == 'Podcaster':
                            cursor.execute("INSERT INTO marmut.podcaster (email) VALUES (%s)", [email])
                        elif r == 'Artist':
                            # Generate a new UUID for each pemilik_hak_cipta
                            id_pemilik_hak_cipta_artist = uuid.uuid4()
                            # Insert into pemilik_hak_cipta table
                            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta_artist, 0])
                            # Insert into artist table
                            cursor.execute("INSERT INTO marmut.artist (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [uuid.uuid4(), email, id_pemilik_hak_cipta_artist])
                        elif r == 'Songwriter':
                            # Generate a new UUID for each pemilik_hak_cipta
                            id_pemilik_hak_cipta_songwriter = uuid.uuid4()
                            # Insert into pemilik_hak_cipta table
                            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta_songwriter, 0])
                            # Insert into songwriter table
                            cursor.execute("INSERT INTO marmut.songwriter (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [uuid.uuid4(), email, id_pemilik_hak_cipta_songwriter])

                    # If no role is selected, the user is a non-premium user
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

        # Check if any field is empty
        if not email or not password or not name or not contact:
            messages.error(request, 'All fields are required!')
            return redirect('register')

        with connection.cursor() as cursor:
            # Check if email already exists in 'akun' or 'label' table
            cursor.execute("SELECT email FROM marmut.akun WHERE email = %s UNION SELECT email FROM marmut.label WHERE email = %s", [email, email])
            user = cursor.fetchone()

            if user is not None:
                messages.error(request, 'Email already exists!')
                return redirect('register')

            # Generate a UUID for the id field
            id = uuid.uuid4()
            # Generate a UUID for the id_pemilik_hak_cipta field
            id_pemilik_hak_cipta = uuid.uuid4()

            # Insert into pemilik_hak_cipta table
            cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta, 0])

            # Insert into label table
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
