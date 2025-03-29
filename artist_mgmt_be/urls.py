from django.urls import path,include

urlpatterns = [
    path('users/',include('users.urls')),
    path('artist/',include('artist.urls')),
    path('music/',include('music.urls')),
    path('auth/',include('registration.urls')),
]
