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
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing",status=400).to_dict())

        password = f"{fname}{phone[-4:]}"
        hashed_password = hash_password(password)

        gender_map = {"Male": "m", "Female": "f", "Others": "o"}
        gender = gender_map.get(gender.lower(), "o") 

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO Users (first_name, last_name, email, password, phone, gender, dob, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    [fname, lname, email, hashed_password, phone, gender, dob, address]
                )
                 
            result = ServiceResult.as_success("User Added Successfully")           
            return JsonResponse(result.to_dict(), status=200)

    except IntegrityError as e:
        error_message = str(e)
        if "Violation of UNIQUE KEY constraint" in error_message or "duplicate key" in error_message:
            result = ServiceResult.as_failure("Duplicate entry detected",status=400)
        else:
            result = ServiceResult.as_failure("Database error: " + error_message,status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(str(e), status=500)
        return JsonResponse(result.to_dict())
