from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from location.models import Location
from .models import TripList, TripPath
from django.contrib import messages
from django.views.decorators.http import require_POST
from .TSP import Graph, distance
import json

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

    return render(request, "page/favourite/index.html", {
        'locations': locations
    })

@login_required
def my_trip(request):
    user = request.user
    trip_list_id = f"{user.username}-favourite"

    trip_list, _ = TripList.objects.get_or_create(id=trip_list_id, defaults={
        'user': user,
        'name': f"{user.username}'s Favourite Trip"
    })

    if request.method == 'POST':
        path_name = request.POST.get('path_name')
        if not path_name:
            return redirect('my_trip')

        selected_ids = request.POST.getlist('locations')
        if not selected_ids:
            messages.error(request, "Vui lòng chọn ít nhất một địa điểm.")
            return redirect('favourite')

        locations = list(Location.objects.filter(id__in=selected_ids, favourited_by=user))
        if not locations:
            messages.error(request, "Không tìm thấy các địa điểm đã chọn.")
            return redirect('favourite')

        id_to_index = {loc.id: idx for idx, loc in enumerate(locations)}
        index_to_id = {idx: loc.id for idx, loc in enumerate(locations)}
        coordinates = [loc.coordinate for loc in locations]

        pinned_positions = [None] * len(locations)
        fixed_position_flags = [False] * len(locations)
        precedence_constraints = []

        start_id_str = request.POST.get('start_point')
        end_id_str = request.POST.get('end_point')
        start_id = int(start_id_str) if start_id_str and start_id_str.isdigit() else None
        end_id = int(end_id_str) if end_id_str and end_id_str.isdigit() else None

        for loc in locations:
            loc_id = loc.id
            loc_id_str = str(loc_id)
            index = id_to_index[loc_id]

            pinned_str = request.POST.get(f'pinned_order_{loc_id_str}')
            if pinned_str and pinned_str.isdigit():
                pinned_index = int(pinned_str) - 1
                if 0 <= pinned_index < len(locations):
                    pinned_positions[pinned_index] = index
                    fixed_position_flags[pinned_index] = True

            after_id_str = request.POST.get(f'precedence_after_{loc_id_str}')
            if after_id_str and after_id_str.isdigit():
                after_id = int(after_id_str)
                if after_id in id_to_index:
                    precedence_constraints.append((id_to_index[after_id], index))

        # Calculate distances and durations
        distances = []
        durations_map = {}

        for i in range(len(coordinates)):
            for j in range(len(coordinates)):
                if i != j:
                    dist, duration = distance(coordinates[i], coordinates[j])
                    distances.append((i, j, dist))
                    durations_map[(i, j)] = duration

        graph = Graph(len(locations))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        start_index = id_to_index.get(start_id) if start_id in id_to_index else None
        end_index = id_to_index.get(end_id) if end_id in id_to_index else None

        path, cost = graph.find_hamiltonian_path(
            fixed_position=fixed_position_flags,
            precedence_constraints=precedence_constraints,
            start=start_index,
            end=end_index
        )

        if path is None:
            messages.error(request, "Không thể tạo lịch trình hợp lệ với các ràng buộc đã chọn.")
            return redirect('favourite')

        total_duration = sum(
            durations_map.get((path[i], path[i+1]), 0) for i in range(len(path) - 1)
        )

        ordered_location_ids = [index_to_id[i] for i in path]

        # Determine actual start and end Location objects
        start_point_obj = next((loc for loc in locations if loc.id == start_id), None)
        end_point_obj = next((loc for loc in locations if loc.id == end_id), None)

        TripPath.objects.create(
            trip_list=trip_list,
            path_name=path_name,
            locations_ordered=json.dumps(ordered_location_ids),
            total_distance=cost,
            total_duration=total_duration,
            start_point=start_point_obj,
            end_point=end_point_obj
        )

        # Unfavorite the locations that were just used
        for loc in locations:
            loc.favourited_by.remove(user)

        return redirect('my_trip')

    trip_paths = TripPath.objects.filter(trip_list=trip_list).order_by('-created_at')
    all_ids = []
    parsed_trip_paths = []

    for path in trip_paths:
        try:
            loc_ids = json.loads(path.locations_ordered)
        except json.JSONDecodeError:
            loc_ids = []

        all_ids.extend(loc_ids)

        parsed_trip_paths.append({
            'id': path.id,
            'path_name': path.path_name,
            'locations': loc_ids,
            'start_point': path.start_point.location if path.start_point else None,
            'end_point': path.end_point.location if path.end_point else None,
            'total_distance': round(path.total_distance / 1000, 1) if path.total_distance is not None else None,
            'total_duration': round(path.total_duration / 60, 1) if path.total_duration is not None else None,
            'created_at': path.created_at,
        })

    location_qs = Location.objects.filter(id__in=all_ids)
    location_map = {loc.id: loc.location for loc in location_qs}

    return render(request, 'my_trip.html', {
        'trip_paths': parsed_trip_paths,
        'location_map': location_map
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