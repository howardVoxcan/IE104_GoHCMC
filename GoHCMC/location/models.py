from django.db import models
from django.contrib.auth.models import User
from datetime import time
from django.contrib.auth import get_user_model
from sympy import true 
import uuid

# Create your models here.
User = get_user_model()
class LocationQuerySet(models.QuerySet):
    def open_at(self, desired_time):
        return self.filter(
            models.Q(open_time__lte=desired_time, close_time__gte=desired_time) |
            models.Q(open_time__gt=models.F('close_time')) & (
                models.Q(open_time__lte=desired_time) | models.Q(close_time__gte=desired_time)
            )
        )
    
class Location_List(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE,related_name = "location_list")
    name = models.CharField(max_length = 50, default = "")

    def __str__(self):
        return self.name

class Location(models.Model):
    favourited_by = models.ManyToManyField(User, related_name="favourite_locations", blank=True)
    code = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length = 64)
    type = models.CharField(max_length=18, default = "")
    tags = models.TextField(default = "")
    rating = models.FloatField(default = 5)
    open_time = models.TimeField(default = time(0,0))
    close_time = models.TimeField(default = time(23,59))
    ticket_info = models.CharField(max_length = 100, default = "")
    address = models.CharField(max_length = 100, default = "")
    image_path = models.CharField(max_length=255, default='')
    description = models.TextField(default="")
    long_description = models.TextField(default="")
    coordinate = models.CharField(max_length = 40, default = "")

    def __str__(self):
        return f"{self.code} {self.location} : {self.description} "

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments') 
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='comments')  
    content = models.TextField() 
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    bot_reply = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']  # Show newest comments first

    def __str__(self):
        return f"Comment by {self.user.username} on {self.location.location}"