from django.urls import path
from . import views

urlpatterns = [
    path('',views.favourite, name = 'favourite'),
    path('create_trip/', views.create_trip, name = 'create_trip'),
]