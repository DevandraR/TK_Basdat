from django.shortcuts import render, redirect
from django.db import connection  # Import the connection object

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def playlist(request):
    if not request.session.get('user_email'):  # Check if the user is logged in
        return redirect('marmut:login')  # Redirect to the login page if not

    email = request.session['user_email']
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM marmut.user_playlist WHERE email_pembuat = %s", [email])
        playlists = dictfetchall(cursor)  # Get the user's playlists

    return render(request, 'playlist.html', {'playlists': playlists})

def add_playlist(request):
    if not request.session.get('user_email'):  # Check if the user is logged in
        return redirect('marmut:login')  # Redirect to the login page if not

    # Add your logic here to handle the form submission

    return render(request, 'addplaylist.html')

