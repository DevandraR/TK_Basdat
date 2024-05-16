from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
import uuid

def determine_user_type(email, cursor):
    cursor.execute("SELECT email FROM marmut.podcaster WHERE email = %s", [email])
    is_podcaster = cursor.fetchone() is not None

    cursor.execute("SELECT email FROM marmut.premium WHERE email = %s", [email])
    is_premium = cursor.fetchone() is not None

    cursor.execute("SELECT email_akun FROM marmut.artist WHERE email_akun = %s", [email])
    is_artist = cursor.fetchone() is not None

    cursor.execute("SELECT email_akun FROM marmut.songwriter WHERE email_akun = %s", [email])
    is_songwriter = cursor.fetchone() is not None

    cursor.execute("SELECT email FROM marmut.label WHERE email = %s", [email])
    is_label = cursor.fetchone() is not None

    cursor.execute("SELECT email FROM marmut.non_premium WHERE email = %s", [email])
    is_non_premium = cursor.fetchone() is not None

    user_type = {
        'is_podcaster': is_podcaster,
        'is_premium': is_premium,
        'is_artist': is_artist,
        'is_songwriter': is_songwriter,
        'is_label': is_label,
        'is_non_premium': is_non_premium,
    }

    return user_type

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM marmut.akun WHERE email = %s AND password = %s", [email, password])
            user = cursor.fetchone()

            if user is not None:
                request.session['user_email'] = user[0]
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
                return redirect('register')

            # Insert into akun table
            cursor.execute("INSERT INTO marmut.akun (email, password, nama, gender, tempat_lahir, tanggal_lahir, is_verified, kota_asal) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [email, password, name, gender, birthplace, birthdate, len(role) > 0, city])

            # Generate a UUID for the id field
            id = uuid.uuid4()
            # Generate a UUID for the id_pemilik_hak_cipta field
            id_pemilik_hak_cipta = uuid.uuid4()

            # Insert into role table
            for r in role:
                if r == 'Podcaster':
                    cursor.execute("INSERT INTO marmut.podcaster (email) VALUES (%s)", [email])
                elif r == 'Artist':
                    # Insert into pemilik_hak_cipta table
                    cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta, 0])
                    # Insert into artist table
                    cursor.execute("INSERT INTO marmut.artist (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [id, email, id_pemilik_hak_cipta])
                elif r == 'Songwriter':
                    # Insert into pemilik_hak_cipta table
                    cursor.execute("INSERT INTO marmut.pemilik_hak_cipta (id, rate_royalti) VALUES (%s, %s)", [id_pemilik_hak_cipta, 0])
                    # Insert into songwriter table
                    cursor.execute("INSERT INTO marmut.songwriter (id, email_akun, id_pemilik_hak_cipta) VALUES (%s, %s, %s)", [id, email, id_pemilik_hak_cipta])

            # If no role is selected, the user is a non-premium user
            if len(role) == 0:
                cursor.execute("INSERT INTO marmut.non_premium (email) VALUES (%s)", [email])

            messages.success(request, 'Registration successful!')
            return redirect('login')

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
            # Check if email already exists
            cursor.execute("SELECT email FROM marmut.akun WHERE email = %s", [email])
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

def dashboard(request):
    user_email = request.session.get('user_email') 
    user_type = request.session.get('user_type')
    if user_email is None:
        return redirect('login')
    else:
        return render(request, 'dashboard.html', {'user_email': user_email, 'user_type': user_type})