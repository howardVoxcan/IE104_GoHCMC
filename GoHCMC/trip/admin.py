from django.contrib import admin
from .models import TripList, TripPath

# Register your models here.
admin.site.register(TripPath)
admin.site.register(TripList)