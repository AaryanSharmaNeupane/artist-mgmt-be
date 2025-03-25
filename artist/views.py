from django.db import connection, transaction
from django.http import JsonResponse  
from django.db.utils import IntegrityError
import json
import hashlib
from django.views.decorators.csrf import csrf_exempt

from utils.service_result import ServiceResult



@csrf_exempt
def add_artist(request, *args, **kwargs):
    if request.method != "POST":
        result = ServiceResult.as_failure(error_message="Only POST method allowed", status=405)
        return JsonResponse(result.to_dict())

    try:
        data = json.loads(request.body.decode("utf-8"))
        name=data.get("name") 
        dob = data.get("dob")
        gender = data.get("gender")
        address = data.get("address")
        first_release_year = data.get("first_release_year")
        no_of_albums_released = data.get("no_of_albums_released")

        
        required_fields = ["name", "first_release_year", "no_of_albums_released", "gender"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing", status=400).to_dict())

        gender_map = {"male": "m", "female": "f", "others": "o"}
        gender = gender_map.get(gender.lower())

        with transaction.atomic():
            with connection.cursor() as cursor:
 
                cursor.execute(
                    '''
                    INSERT INTO Artist (name, dob,gender, address, first_release_year, no_of_albums_released)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''',
                    [name, dob, gender,  address,first_release_year, no_of_albums_released]
                )
                artist_id = cursor.fetchone()[0] 

        artist_data = {
            "id": artist_id,
            "name": name,
            "dob": dob,
            "gender": gender,
            "address": address,
            "first_release_year": first_release_year,
            "no_of_albums_released": no_of_albums_released,
        }
        
        result = ServiceResult.as_success(artist_data)
        return JsonResponse(result.to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e)
        result = ServiceResult.as_failure("Database error: " + error_message, status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(str(e), status=500)
        return JsonResponse(result.to_dict())

    

@csrf_exempt
def get_artist(request, *args, **kwargs):
    if request.method != "GET":
        result = ServiceResult.as_failure(error_message="Only GET method allowed", status=405)
        return JsonResponse(result.to_dict())

    try:
        gender_map = {"m": "male", "f": "female", "o": "others"}

        with transaction.atomic():
            with connection.cursor() as cursor:
                if "id" in kwargs:
                    artist_id = kwargs.get("id")
                    cursor.execute(
                        '''
                        SELECT id, name, dob, gender, address,first_release_year, no_of_albums_released
                        FROM Artist WHERE id = %s
                        ''', 
                        [artist_id]
                    )
                    artist = cursor.fetchone()

                    if not artist:
                        return JsonResponse(ServiceResult.as_failure("Artist not found", status=404).to_dict())

                    artist_data = {
                        "id": artist[0],
                        "name": artist[1],
                        "dob": artist[2],
                        "gender": gender_map.get(artist[3]),
                        "address": artist[4],
                        "first_release_year": artist[5],
                        "no_of_albums_released": artist[6],
                    }

                    return JsonResponse(ServiceResult.as_success(artist_data).to_dict())

                cursor.execute(
                    '''
                    SELECT id, name, dob, gender, address,first_release_year, no_of_albums_released
                    FROM Artist ORDER BY ID DESC
                    '''
                )
                artists = cursor.fetchall()

                if not artists:
                    return JsonResponse(ServiceResult.as_failure("No artist found", status=404).to_dict())

                artists_data = [
                    {
                        "id": artist[0],
                        "name": artist[1],
                        "dob": artist[2],
                        "gender": gender_map.get(artist[3]),
                        "address": artist[4],
                        "first_release_year": artist[5],
                        "no_of_albums_released": artist[6],
                    }
                    for artist in artists
                ]

                return JsonResponse(ServiceResult.as_success(artists_data).to_dict())

    except IntegrityError as e:
        error_message = str(e)
        result = ServiceResult.as_failure("Database error: " + error_message, status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e),status=500).to_dict())


@csrf_exempt
def delete_artist(request, *args, **kwargs):
    if request.method != "DELETE":
        return JsonResponse(ServiceResult.as_failure("Only DELETE method allowed", status=405).to_dict(), status=405)

    try:
        artist_id = kwargs.get("id")
        if not artist_id:
            return JsonResponse(ServiceResult.as_failure("Artist ID is required", status=400).to_dict(), status=400)

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    DELETE FROM Artist WHERE id = %s
                    ''',
                    [artist_id]
                )

                if cursor.rowcount == 0:
                    return JsonResponse(ServiceResult.as_failure("Artist not found", status=404).to_dict(), status=404)

        return JsonResponse(ServiceResult.as_success("Artist deleted successfully").to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e).lower()
        if "foreign key constraint" in error_message or "violates foreign key constraint" in error_message:
            return JsonResponse(ServiceResult.as_failure(
                "This artist is referenced in another table. Please remove related entries before proceeding.",
                status=400
            ).to_dict(), status=400)
        return JsonResponse(ServiceResult.as_failure("Database error: " + error_message, status=400).to_dict(), status=400)

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict(), status=500)




@csrf_exempt
def update_users(request, *args, **kwargs):
    if request.method != "PUT":
        return JsonResponse(ServiceResult.as_failure("Only PUT method allowed", status=405).to_dict())

    try:
        data = json.loads(request.body.decode("utf-8"))
        artist_id = data.get("id")

        if not artist_id:
            return JsonResponse(ServiceResult.as_failure("Artist ID is required", status=400).to_dict())

        name = data.get("name")
        dob = data.get("dob")
        gender = data.get("gender")
        address = data.get("address")
        first_release_year = data.get("first_release_year")
        no_of_albums_released = data.get("no_of_albums_released")

        required_fields = ["name", "first_release_year", "no_of_albums_released", "gender"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure("Required fields missing", status=400).to_dict())

        gender_map = {"male": "m", "female": "f", "others": "o"}
        gender = gender_map.get(gender.lower())

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    UPDATE Artist 
                    SET name = %s, dob = %s, gender = %s, address = %s, 
                        first_release_year = %s, no_of_albums_released = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    ''',
                    [name, dob, gender, address, first_release_year, no_of_albums_released, artist_id]
                )

                if cursor.rowcount == 0:
                    return JsonResponse(ServiceResult.as_failure("Artist ID not found", status=404).to_dict())

        artist_data = {
            "id": artist_id,
            "name": name,
            "dob": dob,
            "gender": gender,
            "address": address,
            "first_release_year": first_release_year,
            "no_of_albums_released": no_of_albums_released,
        }

        return JsonResponse(ServiceResult.as_success(artist_data).to_dict())

    except IntegrityError as e:
        error_message = str(e)
        return JsonResponse(ServiceResult.as_failure("Database error: " + error_message, status=400).to_dict())

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict())
