from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('locations', views.locations, name = 'locations'),
    path('<str:location_code>/',views.display_location, name='display_location'),
    path('<str:location_code>/submit_comment_ajax/', views.submit_comment_ajax, name='submit_comment_ajax'),
]
