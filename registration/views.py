import datetime
import hashlib
import json
import jwt
from django.db import connection, IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from utils.service_result import ServiceResult
from django.conf import settings



def hash_password(password):
    sha1 = hashlib.sha1()
    sha1.update(password.encode('utf-8'))
    return sha1.hexdigest()

def generate_jwt_token(user_id, username, is_admin):
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            hours=1
        )
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
@csrf_exempt
def register(request):
    if request.method != "POST":
        result = ServiceResult.as_failure(error_message="Only POST method allowed", status=405)
        return JsonResponse(result.to_dict())
    
    try:
        data = json.loads(request.body.decode("utf-8"))

        required_fields = ['fname', 'lname', 'email', 'username', 'password']
        missing_fields = [field for field in required_fields if data.get(field) in [None, ""]]
        if missing_fields:
            return JsonResponse(ServiceResult.as_failure(error_message="Required fields missing", status=400).to_dict())

       
        hashed_password = hash_password(data['password'])
        
        with connection.cursor() as cursor:    
            cursor.execute(
                '''
                INSERT INTO auth_user 
                (password, is_superuser, username, first_name, last_name, 
                 email, is_staff, is_active, date_joined) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ''',
                [
                    hashed_password,
                    False,
                    data['username'],
                    data['fname'],
                    data['lname'],
                    data['email'],
                    True,  
                    True   
                ]
            )

            if cursor.rowcount == 1:
                result = ServiceResult.as_success("User registered successfully")
                return JsonResponse(result.to_dict())
                
    except IntegrityError as e:
        error_message = str(e)
        if "username" in error_message.lower():
            result = ServiceResult.as_failure("Username already exists", status=400)
        elif "email" in error_message.lower():
            result = ServiceResult.as_failure("Email already exists", status=400)
        else:
            result = ServiceResult.as_failure("Database error", status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(f"Server error: {str(e)}", status=500)
        return JsonResponse(result.to_dict())
    

@csrf_exempt
def login(request):
    if request.method != "POST":
        result = ServiceResult.as_failure(error_message="Only POST method allowed", status=405)
        return JsonResponse(result.to_dict())
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        required_fields = ['username', 'password']
        missing_fields = [field for field in required_fields if data.get(field) in [None, ""]]
        if missing_fields:
            return JsonResponse(
                ServiceResult.as_failure(
                    error_message="Required fields missing",
                    status=400
                ).to_dict()
            )

        with connection.cursor() as cursor:    
            cursor.execute(
                '''
                SELECT id, username, is_staff FROM auth_user 
                WHERE username = %s AND password = %s
                ''',   
                [
                    data['username'],
                    hash_password(data['password'])
                ]
            )
            user = cursor.fetchone()
            if not user:
                result = ServiceResult.as_failure("Invalid username or password", status=401)
                return JsonResponse(result.to_dict())

           
            token = generate_jwt_token(user[0], user[1], user[2]) 
           
            response = JsonResponse(
                ServiceResult.as_success({ 
            "token":token
                }).to_dict()
            )
                 
            return response
            
    except IntegrityError as e:
        result = ServiceResult.as_failure("Database error", status=400)
        return JsonResponse(result.to_dict())

    except Exception as e:
        result = ServiceResult.as_failure(f"Server error: {str(e)}", status=500)
        return JsonResponse(result.to_dict())




@csrf_exempt
def validate_token(request):
    if request.method != "POST":
        return JsonResponse(
            ServiceResult.as_failure(
                error_message="Only POST method allowed", 
                status=405
            ).to_dict()
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
        token=data['token']
        if not token:
            return JsonResponse(
                ServiceResult.as_failure(
                    "Token is required", 
                    status=400
                ).to_dict()
            )

        try:
            decoded_token = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            return JsonResponse(
                ServiceResult.as_success({
                    "user_id": decoded_token.get("user_id"),
                    "username": decoded_token.get("username"),
                    "expires_at": decoded_token.get("exp"),
                }).to_dict()
            )

        except jwt.ExpiredSignatureError:
            return JsonResponse(
                ServiceResult.as_failure(
                    "Token has expired", 
                    status=401
                ).to_dict()
            )
        except jwt.InvalidTokenError as e:
            return JsonResponse(
                ServiceResult.as_failure(
                    f"Invalid token: {str(e)}", 
                    status=401
                ).to_dict()
            )

    except Exception as e:
        return JsonResponse(
            ServiceResult.as_failure(
                f"Server error: {str(e)}", 
                status=500
            ).to_dict()
        )