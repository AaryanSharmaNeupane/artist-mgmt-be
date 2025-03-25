from django import urls
from artist import views

urlpatterns = [
    urls.path('add/',views.add_artist),
    urls.path('get/',views.get_artist),
    urls.path('get/<int:id>/',views.get_artist),
    urls.path('delete/<int:id>/',views.delete_artist),
    urls.path('update/',views.update_artist)
]