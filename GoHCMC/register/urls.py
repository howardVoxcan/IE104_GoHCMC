from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('logout/', views.logout_view, name='logout'),
]
