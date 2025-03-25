import requests

response = requests.post(
    "http://127.0.0.1:5111/users/add/", 
    json={
        "fname": "admin",
        "lname": "admin",
        "email": "admin@gmail.com",
        "phone": "1234567890",
        "gender": "Male",
        "dob": "2000-01-01",
        "address": "xyz"
    }
)

print(response.json())
