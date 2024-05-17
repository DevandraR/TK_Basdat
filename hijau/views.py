from django.shortcuts import render, redirect
from django.db import connection

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def playlist(request):
    if not request.session.get('user_email'):
        return redirect('marmut:login')

    email = request.session['user_email']
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE email_pembuat = %s", [email])
        playlists = dictfetchall(cursor)

    return render(request, 'playlist.html', {'playlists': playlists})

def detail_playlist(request, id_user_playlist):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist = dictfetchall(cursor)[0]  # Get the playlist details

    return render(request, 'detailplaylist.html', {'playlist': playlist})

def change_playlist(request, id_user_playlist):
    if request.method == 'POST':
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']

        with connection.cursor() as cursor:
            cursor.execute("UPDATE marmut.user_playlist SET judul = %s, deskripsi = %s WHERE id_user_playlist = %s", [judul, deskripsi, id_user_playlist])

        return redirect('hijau:playlist')

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist = dictfetchall(cursor)[0]  # Get the playlist details

    return render(request, 'changeplaylist.html', {'playlist': playlist})

def delete_playlist(request, id_user_playlist):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])

    return redirect('hijau:playlist')

def add_playlist(request):
    if not request.session.get('user_email'):
        return redirect('marmut:login')

    if request.method == 'POST':
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO marmut.user_playlist (email_pembuat, judul, deskripsi) VALUES (%s, %s, %s)", [request.session['user_email'], judul, deskripsi])

        return redirect('hijau:playlist')

    return render(request, 'addplaylist.html')
