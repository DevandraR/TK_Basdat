from datetime import datetime, timezone
from django.shortcuts import render, redirect
from django.db import connection
import uuid
from django.contrib import messages


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

    if request.method == 'POST':
        if 'play' in request.POST:
            id_song = request.POST['play']
            timestamp = datetime.now()
            email_pemain = request.session['user_email']  # Assuming the email is stored in session
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO marmut.akun_play_song (email_pemain, id_song, waktu) VALUES (%s, %s, %s)", [email_pemain, id_song, timestamp])
                cursor.execute("UPDATE marmut.song SET total_play = total_play + 1 WHERE id_konten = %s", [id_song])
        elif 'delete' in request.POST:
            id_song = request.POST['delete']
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM marmut.playlist_song WHERE id_playlist = %s AND id_song = %s", [playlist['id_playlist'], id_song])

    with connection.cursor() as cursor:
        # Join the playlist_song, song, konten, and akun tables to get the song details
        cursor.execute("""
            SELECT k.judul, a.nama as artist, k.durasi, s.id_konten as id_song
            FROM marmut.playlist_song ps
            JOIN marmut.song s ON ps.id_song = s.id_konten
            JOIN marmut.konten k ON s.id_konten = k.id
            JOIN marmut.artist ar ON s.id_artist = ar.id
            JOIN marmut.akun a ON ar.email_akun = a.email
            WHERE ps.id_playlist = %s
        """, [playlist['id_playlist']])
        songs = dictfetchall(cursor)  # Get the songs in the playlist

        # Calculate the total number of songs and total duration
        total_durasi = sum(song['durasi'] for song in songs)
        jumlah_lagu = len(songs)

        # Update the playlist with the new total duration and number of songs
        cursor.execute("""
            UPDATE marmut.user_playlist
            SET jumlah_lagu = %s, total_durasi = %s
            WHERE id_user_playlist = %s
        """, [jumlah_lagu, total_durasi, id_user_playlist])

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
                cursor.execute("UPDATE marmut.song SET total_play = total_play + 1 WHERE id_konten = %s", [song[0]])

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

def song_detail(request, id_song):
    with connection.cursor() as cursor:
        # Get the song details
        cursor.execute("""
            SELECT k.judul, a.nama as artist, k.durasi, s.id_konten as id_song, k.tanggal_rilis, k.tahun, s.total_play, s.total_download, al.judul as album
            FROM marmut.song s
            JOIN marmut.konten k ON s.id_konten = k.id
            JOIN marmut.artist ar ON s.id_artist = ar.id
            JOIN marmut.akun a ON ar.email_akun = a.email
            LEFT JOIN marmut.album al ON s.id_album = al.id
            WHERE s.id_konten = %s
        """, [id_song])
        song = dictfetchall(cursor)[0]

        # Get the song's genres
        cursor.execute("""
            SELECT genre
            FROM marmut.genre
            WHERE id_konten = %s
        """, [id_song])
        genres = [row[0] for row in cursor.fetchall()]

        # Get the song's songwriters
        cursor.execute("""
            SELECT a.nama
            FROM marmut.songwriter sw
            JOIN marmut.songwriter_write_song sws ON sw.id = sws.id_songwriter
            JOIN marmut.akun a ON sw.email_akun = a.email
            WHERE sws.id_song = %s
        """, [id_song])
        songwriters = [row[0] for row in cursor.fetchall()]

    song['genres'] = genres
    song['songwriters'] = songwriters

    return render(request, 'playsong.html', {'song': song})

def play_song(request, id_song):
    if request.method == 'POST':
        progress = int(request.POST['progress'])
        if progress > 70:
            timestamp = datetime.now()
            email_pemain = request.session['user_email']  # Assuming the email is stored in session
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO marmut.akun_play_song (email_pemain, id_song, waktu) VALUES (%s, %s, %s)", [email_pemain, id_song, timestamp])
                cursor.execute("UPDATE marmut.song SET total_play = total_play + 1 WHERE id_konten = %s", [id_song])


    with connection.cursor() as cursor:
        # Get the song details
        cursor.execute("""
            SELECT k.judul, a.nama as artist, k.durasi, s.id_konten as id_song, k.tanggal_rilis, k.tahun, s.total_play, s.total_download, al.judul as album
            FROM marmut.song s
            JOIN marmut.konten k ON s.id_konten = k.id
            JOIN marmut.artist ar ON s.id_artist = ar.id
            JOIN marmut.akun a ON ar.email_akun = a.email
            LEFT JOIN marmut.album al ON s.id_album = al.id
            WHERE s.id_konten = %s
        """, [id_song])
        song = dictfetchall(cursor)[0]

        # Get the song's genres
        cursor.execute("""
            SELECT genre
            FROM marmut.genre
            WHERE id_konten = %s
        """, [id_song])
        genres = [row[0] for row in cursor.fetchall()]

        # Get the song's songwriters
        cursor.execute("""
            SELECT a.nama
            FROM marmut.songwriter sw
            JOIN marmut.songwriter_write_song sws ON sw.id = sws.id_songwriter
            JOIN marmut.akun a ON sw.email_akun = a.email
            WHERE sws.id_song = %s
        """, [id_song])
        songwriters = [row[0] for row in cursor.fetchall()]

    song['genres'] = genres
    song['songwriters'] = songwriters

    return render(request, 'playsong.html', {'song': song})

# views.py
def download_song(request, id_song):
    email_pemain = request.session['user_email']  # Assuming the email is stored in session
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.downloaded_song WHERE id_song = %s AND email_downloader = %s", [id_song, email_pemain])
        song_already_downloaded = cursor.fetchone()
        if song_already_downloaded:
            # Song has already been downloaded by this user
            cursor.execute("SELECT judul FROM marmut.konten WHERE id = %s", [id_song])
            song_title = cursor.fetchone()[0]
            return render(request, 'already_downloaded.html', {'song': {'judul': song_title}})
        else:
            # Download the song
            cursor.execute("INSERT INTO marmut.downloaded_song (id_song, email_downloader) VALUES (%s, %s)", [id_song, email_pemain])
            cursor.execute("UPDATE marmut.song SET total_download = total_download + 1 WHERE id_konten = %s", [id_song])
            cursor.execute("SELECT judul FROM marmut.konten WHERE id = %s", [id_song])
            song_title = cursor.fetchone()[0]
            return render(request, 'download_success.html', {'song': {'judul': song_title}})

def add_to_playlist(request, id_song):
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE email_pembuat = %s", [email])
        playlists = dictfetchall(cursor)

    if not playlists:
        messages.error(request, "Anda belum membuat playlist. Silakan buat playlist terlebih dahulu.")
        return redirect('song_detail', id_song=id_song)

    return render(request, 'add_to_playlist.html', {'playlists': playlists, 'song_id': id_song})

# Function untuk memproses penambahan lagu ke playlist
def submit_add_to_playlist(request, id_song):
    if not request.session.get('user_email'):
        return redirect('login')

    email = request.session['user_email']
    id_user_playlist = request.POST['playlist']

    with connection.cursor() as cursor:
        cursor.execute("SELECT id_playlist FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        id_playlist = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM marmut.playlist_song WHERE id_playlist = %s AND id_song = %s", [id_playlist, id_song])
        if cursor.fetchone() is not None:
            cursor.execute("SELECT judul FROM marmut.konten WHERE id = %s", [id_song])
            song_title = cursor.fetchone()[0]
            cursor.execute("SELECT judul FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
            playlist_title = cursor.fetchone()[0]
            return render(request, 'add_to_playlist_result.html', {'success': False, 'song_title': song_title, 'playlist_title': playlist_title, 'song_id': id_song, 'playlist_id': id_user_playlist})

        cursor.execute("INSERT INTO marmut.playlist_song (id_playlist, id_song) VALUES (%s, %s)", [id_playlist, id_song])
        cursor.execute("SELECT judul FROM marmut.konten WHERE id = %s", [id_song])
        song_title = cursor.fetchone()[0]
        cursor.execute("SELECT judul FROM marmut.user_playlist WHERE id_user_playlist = %s", [id_user_playlist])
        playlist_title = cursor.fetchone()[0]

    return render(request, 'add_to_playlist_result.html', {'success': True, 'song_title': song_title, 'playlist_title': playlist_title, 'song_id': id_song, 'playlist_id': id_user_playlist})