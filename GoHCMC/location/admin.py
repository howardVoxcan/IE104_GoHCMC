from django.contrib import admin
from .models import Location, Location_List, Comment

# Register your models here.
admin.site.register(Location)
admin.site.register(Location_List)
admin.site.register(Comment)