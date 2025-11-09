from django.urls import path
from . import views

urlpatterns = [
    path('',views.favourite, name = 'favourite'),
    path('my_trip/', views.my_trip, name = 'my_trip'),
    path('<int:path_id>/delete_tripPath', views.delete_tripPath, name='delete_tripPath'),
]