from django import urls
from users import views

urlpatterns = [
    urls.path('add/',views.add_users),
]
