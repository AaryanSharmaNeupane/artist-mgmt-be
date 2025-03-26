from django import urls
from music import views


urlpatterns = [
    urls.path('add/',views.add_music),
    urls.path('get/',views.get_music),
    urls.path('get/<int:id>/',views.get_music),
    urls.path('delete/<int:id>/',views.delete_music),
    urls.path('update/',views.update_music)
]
