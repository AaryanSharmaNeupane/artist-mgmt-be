from django.db import connection, transaction
from django.http import JsonResponse  
from django.db.utils import IntegrityError
import json
from django.views.decorators.csrf import csrf_exempt

from utils.service_result import ServiceResult



@csrf_exempt
def add_music(request, *args, **kwargs):
    if request.method != "POST":
        result = ServiceResult.as_failure(error_message="Only POST method allowed", status=405)
        return JsonResponse(result.to_dict())

    try:
        data = json.loads(request.body.decode("utf-8"))
        artist_id=data.get("artist_id") 
        title = data.get("title")
        album_name = data.get("album_name")
        genre = data.get("genre")

        required_fields = ["artist_id", "title", "album_name", "genre"]
        missing_fields = [field for field in required_fields if data.get(field) in [None, ""]]
     
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing", status=400).to_dict())

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO Music (artist_id, title, album_name, genre)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s)
                    ''',
                    [artist_id, title, album_name, genre]
                )
                row = cursor.fetchone()
                if not row:
                    raise Exception("Failed to insert record") 
                music_id = row[0]

        music_data = {
            "id": music_id,
            "artist_id": artist_id,
            "title": title,
            "album_name": album_name,
            "genre": genre    
        }
        
        result = ServiceResult.as_success(music_data)
        return JsonResponse(result.to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e)
        result = ServiceResult.as_failure("Database error: " + error_message, status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(str(e), status=500)
        return JsonResponse(result.to_dict())

    

@csrf_exempt
def get_music(request, *args, **kwargs):
    if request.method != "GET":
        return JsonResponse(ServiceResult.as_failure(error_message="Only GET method allowed", status=405).to_dict())
    try:
        artist_id = request.GET.get("artist_id") 
        with connection.cursor() as cursor:
            if artist_id:
                cursor.execute(
                    '''
                    SELECT Music.id, Music.title, Music.album_name, Music.genre, Artist.artist_name
                    FROM Music
                    INNER JOIN Artist ON Music.artist_id = Artist.id
                    WHERE Music.artist_id = %s
                    ''', 
                    [artist_id]
                )
                musics = cursor.fetchall()
                if not musics:
                    return JsonResponse(ServiceResult.as_failure("No music found for the given artist", status=404).to_dict())

                music_data = [
                    {
                        "id": music[0],
                        "title": music[1],
                        "album_name": music[2],
                        "genre": music[3],
                        "artist_name": music[4]
                    }
                    for music in musics
                ]

                return JsonResponse(ServiceResult.as_success(music_data).to_dict())

            cursor.execute(
                '''
                SELECT id, title, album_name, genre
                FROM Music ORDER BY ID DESC
                '''
            )
            musics = cursor.fetchall()

            if not musics:
                return JsonResponse(ServiceResult.as_failure("No music found", status=404).to_dict())

            musics_data = [
                {
                    "id": music[0],
                    "title": music[1],
                    "album_name": music[2],
                    "genre": music[3],
                }
                for music in musics
            ]

            return JsonResponse(ServiceResult.as_success(musics_data).to_dict())

    except IntegrityError as e:
        return JsonResponse(ServiceResult.as_failure(error_message="Database error: " + str(e), status=400).to_dict())

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(error_message=str(e), status=500).to_dict())


@csrf_exempt
def delete_music(request, *args, **kwargs):
    if request.method != "DELETE":
        return JsonResponse(ServiceResult.as_failure("Only DELETE method allowed", status=405).to_dict(), status=405)
    try:
        music_id = request.GET.get("id")  
        if not music_id:
            return JsonResponse(ServiceResult.as_failure("Music ID is required", status=400).to_dict(), status=400)

        with connection.cursor() as cursor:
            cursor.execute(
                '''
                DELETE FROM Music WHERE id = %s
                ''',
                [music_id]
            )

            if cursor.rowcount == 0:
                return JsonResponse(ServiceResult.as_failure("Music not found", status=404).to_dict(), status=404)

        return JsonResponse(ServiceResult.as_success("Music deleted successfully").to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e).lower()
        return JsonResponse(ServiceResult.as_failure("Database error: " + error_message, status=400).to_dict(), status=400)
    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict(), status=500)

@csrf_exempt
def update_music(request, *args, **kwargs):
    if request.method != "PUT":
        return JsonResponse(ServiceResult.as_failure("Only PUT method allowed", status=405).to_dict(), status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        music_id = data.get("id")
        artist_id = data.get("artist_id")
        title = data.get("title")
        album_name = data.get("album_name")
        genre = data.get("genre")

        required_fields = ["artist_id", "title", "album_name", "genre"]
        missing_fields = [field for field in required_fields if data.get(field) in [None, ""]]

        if missing_fields:
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing", status=400).to_dict())

        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE Music 
                SET artist_id = %s, title = %s, album_name = %s, genre = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                ''',
                [artist_id, title, album_name, genre, music_id]
            )

            if cursor.rowcount == 0:
                return JsonResponse(ServiceResult.as_failure("Music ID not found", status=404).to_dict(), status=404)

        return JsonResponse(ServiceResult.as_success("Music updated successfully").to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e)
        return JsonResponse(ServiceResult.as_failure("Database error: " + error_message, status=400).to_dict(), status=400)

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict(), status=500)
