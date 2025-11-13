from django.urls import path
from . import views

urlpatterns = [
    path('', views.trips, name='trip'),
]
