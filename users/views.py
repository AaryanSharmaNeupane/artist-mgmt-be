from django.db import connection, transaction
from django.http import JsonResponse  
from django.db.utils import IntegrityError
import json
import hashlib
from django.views.decorators.csrf import csrf_exempt

from utils.service_result import ServiceResult

def hash_password(password):
    sha1 = hashlib.sha1()
    sha1.update(password.encode('utf-8'))
    return sha1.hexdigest()

@csrf_exempt
def add_users(request, *args, **kwargs):
    if request.method != "POST":
        result = ServiceResult.as_failure(error_message="Only POST method allowed", status=405)
        return JsonResponse(result.to_dict())

    try:
        data = json.loads(request.body.decode("utf-8"))
        fname = data.get("fname")
        lname = data.get("lname")
        email = data.get("email")
        phone = data.get("phone")
        gender = data.get("gender")
        dob = data.get("dob")
        address = data.get("address")
        
        required_fields = ["fname", "lname", "phone", "gender"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing", status=400).to_dict())

        password = f"{fname}{phone[-4:]}"
        hashed_password = hash_password(password)

        gender_map = {"male": "m", "female": "f", "others": "o"}
        gender = gender_map.get(gender.lower())

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO Users (first_name, last_name, email, password, phone, gender, dob, address)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    [fname, lname, email, hashed_password, phone, gender, dob, address]
                )
                user_id = cursor.fetchone()[0] 

        user_data = {
            "id": user_id,
            "fname": fname,
            "lname": lname,
            "email": email,
            "phone": phone,
            "gender": gender,
            "dob": dob,
            "address": address
        }
        
        result = ServiceResult.as_success(user_data)
        return JsonResponse(result.to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e)
        if "Violation of UNIQUE KEY constraint" in error_message or "duplicate key" in error_message:
            result = ServiceResult.as_failure("Duplicate entry detected", status=400)
        else:
            result = ServiceResult.as_failure("Database error: " + error_message, status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(str(e), status=500)
        return JsonResponse(result.to_dict())

    

@csrf_exempt
def get_users(request, *args, **kwargs):
    if request.method != "GET":
        result = ServiceResult.as_failure(error_message="Only GET method allowed", status=405)
        return JsonResponse(result.to_dict())

    try:
        gender_map = {"m": "male", "f": "female", "o": "others"}

        with transaction.atomic():
            with connection.cursor() as cursor:
                if "id" in kwargs:
                    user_id = kwargs.get("id")
                    cursor.execute(
                        '''
                        SELECT first_name, last_name, email, phone, gender, dob, address,id
                        FROM Users WHERE id = %s
                        ''', 
                        [user_id]
                    )
                    user = cursor.fetchone()

                    if not user:
                        return JsonResponse(ServiceResult.as_failure("User ID not found", status=404).to_dict())

                    user_data = {
                        "fname": user[0],
                        "lname": user[1],
                        "email": user[2],
                        "phone": user[3],
                        "gender": gender_map.get(user[4]),
                        "dob": user[5],
                        "address": user[6],
                        "id":user[7]
                    }

                    return JsonResponse(ServiceResult.as_success(user_data).to_dict())

                cursor.execute(
                    '''
                    SELECT first_name, last_name, email, phone, gender, dob, address,id
                    FROM Users ORDER BY ID DESC
                    '''
                )
                users = cursor.fetchall()

                if not users:
                    return JsonResponse(ServiceResult.as_failure("No users found", status=404).to_dict())

                users_data = [
                    {
                        "fname": user[0],
                        "lname": user[1],
                        "email": user[2],
                        "phone": user[3],
                        "gender": gender_map.get(user[4]),
                        "dob": user[5],
                        "address": user[6],
                        "id":user[7]
                    }
                    for user in users
                ]

                return JsonResponse(ServiceResult.as_success(users_data).to_dict())

    except IntegrityError as e:
        error_message = str(e)
        result = ServiceResult.as_failure("Database error: " + error_message, status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e),status=500).to_dict())


@csrf_exempt
def delete_users(request, *args, **kwargs):
    if request.method != "DELETE":
        return JsonResponse(ServiceResult.as_failure("Only DELETE method allowed", status=405).to_dict(), status=405)

    try:
        user_id = kwargs.get("id") 
        if not user_id:
            return JsonResponse(ServiceResult.as_failure("User ID is required", status=400).to_dict())

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT * FROM Users WHERE id = %s
                    ''', 
                    [user_id]
                )
                user = cursor.fetchone()
                if not user:
                    return JsonResponse(ServiceResult.as_failure("User ID not found", status=404).to_dict())
                cursor.execute(
                    '''
                    DELETE FROM Users WHERE id = %s
                    ''', 
                    [user_id]
                )

                return JsonResponse(ServiceResult.as_success("User Deleted Successfully").to_dict())

    except IntegrityError as e:
        return JsonResponse(ServiceResult.as_failure("Database error: " + str(e), status=400).to_dict())

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict(), status=500)


@csrf_exempt
def update_users(request, *args, **kwargs):
    if request.method != "PUT":
        return JsonResponse(ServiceResult.as_failure("Only PUT method allowed", status=405).to_dict())

    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        user_id = data.get("id")

        if not user_id:
            return JsonResponse(ServiceResult.as_failure("User ID is required", status=400).to_dict())

        fname = data.get("fname")
        lname = data.get("lname")
        email = data.get("email")  
        phone = data.get("phone")
        original_gender=gender = data.get("gender")
        dob = data.get("dob")
        address = data.get("address")

        required_fields = ["fname", "lname", "phone", "gender"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure("Required fields missing", status=400).to_dict())
        
        gender_map = {"male": "m", "female": "f", "others": "o"}
        gender = gender_map.get(gender.lower())

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT * FROM Users WHERE id = %s
                    ''', 
                    [user_id]
                )
                user = cursor.fetchone()

                if not user:
                    return JsonResponse(ServiceResult.as_failure("User ID not found", status=404).to_dict())
                
                cursor.execute(
                    '''
                    UPDATE Users 
                    SET first_name = %s, last_name = %s, email = %s, phone = %s, gender = %s, dob = %s, address = %s,updated_at=CURRENT_TIMESTAMP
                    WHERE id = %s
                    ''',
                    [fname, lname, email, phone, gender, dob, address, user_id]
                )

                user_data = {
                    "id": user_id,
                    "fname": fname,
                    "lname": lname,
                    "email": email,
                    "phone": phone,
                    "gender": original_gender,
                    "dob": dob,
                    "address": address
                }

        return JsonResponse(ServiceResult.as_success(user_data).to_dict())

    except IntegrityError as e:
        error_message = str(e)
        if "Violation of UNIQUE KEY constraint" in error_message or "duplicate key" in error_message:
            return JsonResponse(ServiceResult.as_failure("Duplicate entry detected", status=400).to_dict())
        else:
            return JsonResponse(ServiceResult.as_failure("Database error: " + error_message, status=400).to_dict(),)

    except Exception as e:
        return JsonResponse(ServiceResult.as_failure(str(e), status=500).to_dict())
