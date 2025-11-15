from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('locations', views.locations, name = 'locations'),
    path('locations/<str:location_code>/',views.location_detail, name='display_location'),
    path('<str:location_code>/submit_comment_ajax/', views.submit_comment_ajax, name='submit_comment_ajax'),
    # path('locations/<int:id>/', views.location_detail, name='location_detail'),
]
