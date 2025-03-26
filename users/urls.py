from django import urls
from users import views

urlpatterns = [
    urls.path('add/',views.add_users),
    urls.path('get/',views.get_users),
    urls.path('get/<int:id>/',views.get_users),
    urls.path('delete',views.delete_users),
    urls.path('update/',views.update_users)
]
