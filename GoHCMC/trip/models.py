from django.db import models

# Create your models here.
from django.db import models
from location.models import Location
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()

class TripList(models.Model):
    id = models.CharField(
        primary_key=True, max_length=255, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trip_lists")
    name = models.CharField(max_length=255, default="My trip list")

    def __str__(self):
        return self.name

class TripPath(models.Model):
    start_point = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="start_paths")
    end_point = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="end_paths")
    trip_list = models.ForeignKey(TripList, on_delete=models.CASCADE, related_name="trip_paths")
    path_name = models.CharField(max_length=255, default = "")
    locations_ordered = models.CharField(max_length = 255)
    total_distance = models.FloatField(null=True, blank=True)
    total_duration = models.FloatField(null=True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    locations = models.ManyToManyField(Location, related_name="trip_paths")

    def __str__(self):
        return self.path_name