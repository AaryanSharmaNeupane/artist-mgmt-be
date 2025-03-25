import requests

# response = requests.post(
#     "http://127.0.0.1:5111/users/add/", 
#     json={
#         "fname": "aaryan",
#         "lname": "sharma",
#         "email": "aaryan@gmail.com",
#         "phone": "9860221380",
#         "gender": "Male",
#         "dob": "2000-01-01",
#         "address": "xyz"
#     }
# )

response = requests.delete(
    "http://127.0.0.1:5111/users/delete/26/", 
)
print(response.json())
