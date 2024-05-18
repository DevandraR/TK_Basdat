import uuid
from django.db import connection
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from marmut.views import determine_user_type

def list_album(request):
    user_type = request.session.get('user_type')
    if user_type is not None:
        if user_type['is_artist'] or user_type['is_songwriter']:


            return render(request, 'album.html')
        else:
            return render(request, 'forbidden.html')
    else:
        return render(request, 'forbidden.html')

def album_and_song(request):
    user_type = request.session.get('user_type')
    if user_type is not None:
        if user_type['is_artist'] or user_type['is_songwriter']:
            return render(request, 'albumandsong.html')
        else:
            return render(request, 'forbidden.html')
    else:
        return render(request, 'forbidden.html')
    
def album_detail(request, album_id):
    email = request.session.get('label_email')
    if email is None:
        return redirect('login')
    
    with connection.cursor() as cursor:
        user_type = request.session.get('user_type')

        if user_type['is_label']:
            cursor.execute(f"""
                            SELECT 
                                k.judul AS Judul_Lagu,
                                k.durasi AS Durasi,
                                s.total_play AS Total_Play,
                                s.total_download AS Total_Download
                            FROM 
                                marmut.song s
                            JOIN 
                                marmut.konten k
                            ON 
                                s.id_konten = k.id
                            JOIN 
                                marmut.album a
                            ON 
                                s.id_album = a.id
                            WHERE 
                                a.id = '{uuid.UUID(album_id)}';
                           """)
            results = cursor.fetchall()
            album = []
            for result in results:
                album.append({
                    'judul_lagu': result[0],
                    'durasi': result[1],
                    'total_play': format(int(result[2]), ',').replace(',', '.'),
                    'total_download': format(int(result[3]), ',').replace(',', '.'),
                })

            return render(request, 'albumdetail.html', {'album_detail': album})
    return render(request, 'albumdetail.html', {'album_detail': album})
    
@csrf_exempt
def kelola_album_and_song(request):
    email = request.session.get('user_email')
    if email is None:
        return redirect('login')
    
    with connection.cursor() as cursor:
        user_type = request.session.get('user_type')

        if user_type['is_label']:
            email = request.session.get('label_email')
            cursor.execute("""
                            SELECT 
                                a.judul,
                                a.jumlah_lagu,
                                a.total_durasi,
                                a.id
                            FROM 
                                marmut.album a
                            JOIN 
                                marmut.label l
                            ON 
                                a.id_label = l.id
                            WHERE 
                                l.email = %s
                           """, [email])
            data = cursor.fetchall()
            result = []
            for row in data:
                result.append({
                    'judul_album': row[0],
                    'jumlah_lagu': row[1],
                    'total_durasi': format(int(row[2]),',').replace(',', '.'),
                    'album_id':row[3],
                })
            return render(request, 'albumandsong.html', {'result': result})
    
    return render(request, 'albumandsong.html')

@csrf_exempt
def create_lagu(request):
    user_type = request.session.get('user_type')

    # Check user type and permissions
    if user_type is None or not (user_type.get('is_artist') or user_type.get('is_songwriter')):
        return render(request, 'forbidden.html')

    if request.method == 'POST':
        # Extract form data
        album_title = request.POST.get('album_title')
        song_title = request.POST.get('song_title')
        artist = request.POST.get('artist')
        songwriters = request.POST.getlist('songwriter')
        genres = request.POST.getlist('genre')
        duration = request.POST.get('duration')

        # Here you would typically save the data to the database
        # Example: Album.objects.create(...)

        # Redirect to the album list page after successful form submission
        return redirect('/merah/list-album')

    # Render the form template if request method is GET
    return render(request, 'createlagu.html')
    
def cek_royalti(request):
    email = request.session.get('user_email')
    print(email)
    if email is None:
        return redirect('login')

    with connection.cursor() as cursor:
        user_type = request.session.get('user_type')

        if user_type['is_artist']:
            cursor.execute("""
                            SELECT 
                                k.judul AS Judul_lagu, 
                                a.judul AS Judul_Album, 
                                s.total_play AS Total_Play, 
                                s.total_download AS Total_Download, 
                                r.jumlah AS Royalti
                            FROM 
                                marmut.artist ar
                            JOIN 
                                marmut.royalti r ON ar.id_pemilik_hak_cipta = r.id_pemilik_hak_cipta
                            JOIN 
                                marmut.song s ON r.id_song = s.id_konten
                            JOIN 
                                marmut.konten k ON s.id_konten = k.id
                            JOIN 
                                marmut.album a ON s.id_album = a.id
                            WHERE 
                                ar.email_akun = %s
                           """, [email])
            data = cursor.fetchall()
            result = []
            for row in data:
                result.append({
                    'judul_lagu': row[0],
                    'judul_album': row[1],
                    'total_play': format(int(row[2]),',').replace(',', '.'),
                    'total_download': format(int(row[3]),',').replace(',', '.'),
                    'royalti': format(int(row[4]),',').replace(',', '.'),
                })
            return render(request, 'royalty.html', {'result': result})
        
        elif user_type['is_songwriter']:
            cursor.execute("""
                            SELECT 
                                k.judul AS Judul_lagu, 
                                a.judul AS Judul_Album, 
                                s.total_play AS Total_Play, 
                                s.total_download AS Total_Download, 
                                r.jumlah AS Royalti
                            FROM 
                                marmut.songwriter sw
                            JOIN 
                                marmut.royalti r ON sw.id_pemilik_hak_cipta = r.id_pemilik_hak_cipta
                            JOIN 
                                marmut.song s ON r.id_song = s.id_konten
                            JOIN 
                                marmut.konten k ON s.id_konten = k.id
                            JOIN 
                                marmut.album a ON s.id_album = a.id
                            WHERE 
                                sw.email_akun = %s
                           """, [email])
            data = cursor.fetchall()
            result = []
            for row in data:
                result.append({
                    'judul_lagu': row[0],
                    'judul_album': row[1],
                    'total_play': format(int(row[2]),',').replace(',', '.'),
                    'total_download': format(int(row[3]),',').replace(',', '.'),
                    'royalti': format(int(row[4]),',').replace(',', '.'),
                })
            return render(request, 'royalty.html', {'result': result})
        
        elif user_type['is_label']:
            email = request.session.get('label_email')
            cursor.execute("""
                            SELECT 
                                k.judul AS Judul_lagu, 
                                a.judul AS Judul_Album, 
                                s.total_play AS Total_Play, 
                                s.total_download AS Total_Download, 
                                r.jumlah AS Royalti
                            FROM 
                                marmut.label l
                            JOIN 
                                marmut.royalti r ON l.id_pemilik_hak_cipta = r.id_pemilik_hak_cipta
                            JOIN 
                                marmut.song s ON r.id_song = s.id_konten
                            JOIN 
                                marmut.konten k ON s.id_konten = k.id
                            JOIN 
                                marmut.album a ON s.id_album = a.id
                            WHERE
                                l.email = %s
                           """, [email])
            data = cursor.fetchall()
            result = []
            for row in data:
                result.append({
                    'judul_lagu': row[0],
                    'judul_album': row[1],
                    'total_play': format(int(row[2]),',').replace(',', '.'),
                    'total_download': format(int(row[3]),',').replace(',', '.'),
                    'royalti': format(int(row[4]),',').replace(',', '.'),
                })
            return render(request, 'royalty.html', {'result': result})
        else:
            return render(request, 'forbidden.html')