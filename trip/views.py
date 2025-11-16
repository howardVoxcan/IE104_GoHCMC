from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from location.models import Location
from favourite.models import TripList, TripPath
from django.contrib import messages
import json
from django.views.decorators.http import require_POST

# Create your views here.
@login_required
def favourite(request):
    if request.method == 'POST' and 'location_code' in request.POST:
        location_code = request.POST.get('location_code')

        if location_code:
            location = Location.objects.filter(code=location_code).first()
            if location and request.user in location.favourited_by.all():
                location.favourited_by.remove(request.user)
                messages.success(request, "Đã xoá địa điểm khỏi danh sách yêu thích.")
                
        return redirect('favourite')

    locations = Location.objects.filter(favourited_by=request.user)

    return render(request, "favourite.html", {
        'locations': locations
    })

@login_required
def trip(request):
    """
    Trả về dữ liệu đúng định dạng template My Trip của bạn:
    - 'trip_paths' là list các dictionary, trong đó 'locations' là **list ID** (đúng kỳ vọng template).
    - 'location_map' là dict {id: tên địa điểm} dùng với custom filter get_item.
    -> Tránh va chạm với M2M `locations` (nếu đưa thẳng model sang template sẽ là manager M2M).
    """
    user = request.user
    trip_list_id = f"{user.username}-favourite"
    trip_list = TripList.objects.filter(id=trip_list_id, user=user).first()

    if not trip_list:
        return render(request, "page/my_trip/index.html", {"trip_paths": [], "location_map": {}})

    trips = (
        TripPath.objects.filter(trip_list=trip_list)
        .select_related("start_point", "end_point")
        .order_by("-created_at")
    )

    all_ids = set()
    payload = []
    for t in trips:
        try:
            ids = json.loads(t.locations_ordered) if t.locations_ordered else []
        except json.JSONDecodeError:
            ids = []
        all_ids.update(ids)

        payload.append({
            "id": t.id,
            "path_name": t.path_name,
            "total_distance": int(t.total_distance / 1000),
            "total_duration": int(t.total_duration / 30),
            # Dùng tên ngắn để so sánh với loc_name trong template (tránh lặp start/end ở between)
            "start_point": t.start_point.location if t.start_point else None,
            "end_point":   t.end_point.location   if t.end_point   else None,
            # Quan trọng: list ID cho vòng lặp trong template
            "locations": ids,
        })

    location_map = dict(
        Location.objects.filter(id__in=all_ids).values_list("id", "location")
    )

    return render(request, "page/my_trip/index.html", {
        "trip_paths": payload,
        "location_map": location_map,
    })

@require_POST
@login_required
def delete_tripPath(request, path_id):
    if request.method != 'POST' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseForbidden()
    trip_path = get_object_or_404(TripPath, pk=path_id)
    if trip_path.trip_list.user != request.user:
        return HttpResponseForbidden()
    trip_path.delete()
    return JsonResponse({'status': 'deleted'})