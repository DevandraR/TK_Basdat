from django.shortcuts import render, redirect
from django.db import connection
import uuid

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

    return render(request, 'detail_playlist.html', {'playlist': playlist})

def change_playlist(request, id_user_playlist):
    if request.method == 'POST':
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']

        with connection.cursor() as cursor:
            cursor.execute("UPDATE marmut.user_playlist SET judul = %s, deskripsi = %s WHERE id_user_playlist = %s", [judul, deskripsi, id_user_playlist])

        return redirect('playlist')

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist = dictfetchall(cursor)[0]  # Get the playlist details

    return render(request, 'change_playlist.html', {'playlist': playlist})

def delete_playlist(request, id_user_playlist):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # Delete the associated records from the akun_play_user_playlist table
            cursor.execute("DELETE FROM marmut.akun_play_user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
            # Then delete the playlist from the user_playlist table
            cursor.execute("DELETE FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])

        return redirect('playlist')

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist = dictfetchall(cursor)[0]  # Get the playlist details

    return render(request, 'delete_playlist.html', {'playlist': playlist})

def add_playlist(request):
    if not request.session.get('user_email'):
        return redirect('marmut:login')

    if request.method == 'POST':
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        id_user_playlist = uuid.uuid4()  # Generate a new UUID

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM marmut.user_playlist WHERE email_pembuat = %s", [request.session['user_email']])
            if cursor.fetchone() is not None:
                # If the email_pembuat already exists, update the associated records in the akun_play_user_playlist table
                cursor.execute("UPDATE marmut.akun_play_user_playlist SET id_user_playlist = %s WHERE id_user_playlist = (SELECT id_user_playlist FROM marmut.user_playlist WHERE email_pembuat = %s)", [id_user_playlist, request.session['user_email']])
                # Then update the record in the user_playlist table
                cursor.execute("UPDATE marmut.user_playlist SET id_user_playlist = %s, judul = %s, deskripsi = %s, jumlah_lagu = 0, tanggal_dibuat = CURRENT_DATE, total_durasi = 0 WHERE email_pembuat = %s", [id_user_playlist, judul, deskripsi, request.session['user_email']])
            else:
                # If the email_pembuat doesn't exist, insert a new record
                cursor.execute("INSERT INTO marmut.user_playlist (email_pembuat, id_user_playlist, judul, deskripsi, jumlah_lagu, tanggal_dibuat, total_durasi) VALUES (%s, %s, %s, %s, 0, CURRENT_DATE, 0)", [request.session['user_email'], id_user_playlist, judul, deskripsi])

        return redirect('hijau:playlist')

    return render(request, 'addplaylist.html')
