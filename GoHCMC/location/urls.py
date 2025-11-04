from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('locations/', views.locations, name='locations'),
    path('locations/<int:id>/', views.location_detail, name='location_detail'),
]
