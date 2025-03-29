from django import urls
from registration import views

urlpatterns = [
    urls.path('register/',views.register), 
    urls.path('login/',views.login),
    urls.path('validate/',views.validate_token),
]