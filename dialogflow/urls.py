from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.dialogflow_webhook, name='dialogflow_webhook'),
]