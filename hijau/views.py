from datetime import datetime, timezone
from django.shortcuts import render, redirect
from django.db import connection
import uuid

from django.urls import reverse

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def playlist(request):
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']
    print("User Email:", email)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE email_pembuat = %s", [email])
        playlists = dictfetchall(cursor)

    return render(request, 'playlist.html', {'playlists': playlists})

def detail_playlist(request, id_user_playlist):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist = dictfetchall(cursor)[0]  # Get the playlist details

        # Join the playlist_song, song, konten, and akun tables to get the song details
        cursor.execute("""
            SELECT k.judul, a.nama as artist, k.durasi
            FROM marmut.playlist_song ps
            JOIN marmut.song s ON ps.id_song = s.id_konten
            JOIN marmut.konten k ON s.id_konten = k.id
            JOIN marmut.artist ar ON s.id_artist = ar.id
            JOIN marmut.akun a ON ar.email_akun = a.email
            WHERE ps.id_playlist = %s
        """, [playlist['id_playlist']])
        songs = dictfetchall(cursor)  # Get the songs in the playlist

    return render(request, 'detail_playlist.html', {'playlist': playlist, 'songs': songs})



def shuffle_play(request, id_user_playlist):
    if request.method == 'POST':
        timestamp = datetime.now()
        email_pemain = request.session['user_email']  # Assuming the email is stored in session
        email_pembuat = request.session['user_email']  # Assuming the email is stored in session

        with connection.cursor() as cursor:
            # Get the corresponding id_playlist from the user_playlist table
            cursor.execute("SELECT id_playlist FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
            id_playlist = cursor.fetchone()[0]

            cursor.execute("INSERT INTO marmut.akun_play_user_playlist (email_pemain, id_user_playlist, email_pembuat, waktu) VALUES (%s, %s, %s, %s)", [email_pemain, id_user_playlist, email_pembuat, timestamp])

            cursor.execute("SELECT id_song FROM marmut.playlist_song WHERE id_playlist = %s", [id_playlist])
            songs = cursor.fetchall()

            for song in songs:
                cursor.execute("INSERT INTO marmut.akun_play_song (email_pemain, id_song, waktu) VALUES (%s, %s, %s)", [email_pemain, song[0], timestamp])

        return redirect(reverse('detail_playlist', args=[id_user_playlist]))

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


def add_song(request, id_user_playlist):
    if not request.session.get('user_email'):
        return redirect('login')

    if request.method == 'POST':
        id_song = request.POST['song']

        with connection.cursor() as cursor:
            # Get the corresponding id_playlist from the user_playlist table
            cursor.execute("SELECT id_playlist FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
            id_playlist = cursor.fetchone()[0]

            # Check if the song is already in the playlist
            cursor.execute("SELECT * FROM marmut.playlist_song WHERE id_playlist = %s AND id_song = %s", [id_playlist, id_song])
            if cursor.fetchone() is not None:
                # If the song is already in the playlist, return an error message
                return render(request, 'addsong.html', {'error': 'This song is already in the playlist.'})

            # If the song is not in the playlist, add it
            cursor.execute("INSERT INTO marmut.playlist_song (id_playlist, id_song) VALUES (%s, %s)", [id_playlist, id_song])

        return redirect('detail_playlist', id_user_playlist=id_user_playlist)

    with connection.cursor() as cursor:
        # Join the song, konten, artist, and akun tables to get the song title and artist name
        cursor.execute("SELECT s.id_konten, k.judul, a.nama as artist FROM marmut.song s JOIN marmut.konten k ON s.id_konten = k.id JOIN marmut.artist ar ON s.id_artist = ar.id JOIN marmut.akun a ON ar.email_akun = a.email")
        songs = dictfetchall(cursor)  # Get all songs

    return render(request, 'addsong.html', {'songs': songs})


def add_playlist(request):
    if not request.session.get('user_email'):
        return redirect('login')

    if request.method == 'POST':
        email_pembuat = request.session['user_email']
        id_user_playlist = uuid.uuid4()
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        jumlah_lagu = 0
        tanggal_dibuat = datetime.now()
        total_durasi = 0

        with connection.cursor() as cursor:
            # Create a new playlist first
            id_playlist = uuid.uuid4()
            cursor.execute("INSERT INTO marmut.playlist (id) VALUES (%s)", [id_playlist])

            cursor.execute("INSERT INTO marmut.user_playlist (email_pembuat, id_user_playlist, judul, deskripsi, jumlah_lagu, tanggal_dibuat, id_playlist, total_durasi) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [email_pembuat, id_user_playlist, judul, deskripsi, jumlah_lagu, tanggal_dibuat, id_playlist, total_durasi])

        return redirect('playlist')

    return render(request, 'addplaylist.html')
