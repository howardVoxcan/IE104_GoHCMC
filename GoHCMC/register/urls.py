from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]
