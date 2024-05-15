from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def homepage(request):
    return render(request, 'homepage.html')

def register(request):
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM marmut.akun WHERE email = %s AND password = %s", [email, password])
            user = cursor.fetchone()

            if user is not None:
                request.session['user_email'] = user[0]

                # Determine user type here
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

                request.session['user_type'] = user_type

                return redirect('dashboard')
            else:
                messages.error(request, 'Email or password is incorrect!')
                return redirect('login')
    else:
        return render(request, 'login.html')


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