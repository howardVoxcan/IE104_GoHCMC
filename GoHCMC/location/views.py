from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

def homepage(request):
    return render(request, "page/home/index.html")
def locations(request):
    # Logic to retrieve and display a list of locations
    return render(request, "page/locations/index.html")
def location_detail(request, id):
    # Logic to retrieve and display details of a specific location by id
    return render(request, "page/locations/detail.html", {"location_id": id})
