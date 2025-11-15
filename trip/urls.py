from django.urls import path
from . import views

urlpatterns = [
    path('', views.trip, name='trip'),
    path('<int:path_id>/delete_tripPath', views.delete_tripPath, name='delete_tripPath'),
]
