from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from location.models import Location
from .models import TripList, TripPath
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
import sys,os,json
from .TSP import Graph, distance

# Create your views here.
@login_required
def favourite(request):
    user = request.user

    # --- POST Processing (Unfavourite) ---
    if request.method == 'POST' and 'location_code' in request.POST:
        location_code = request.POST.get('location_code')

        if location_code:
            location = Location.objects.filter(code=location_code).first()
            if location and user in location.favourited_by.all():
                location.favourited_by.remove(user)
                # Translated:
                messages.success(request, "Removed location from favourites.")
                
        return redirect('favourite')

    # --- GET Processing (Show page) ---
    
    # 1. Get favourite locations
    locations = Location.objects.filter(favourited_by=user)
    
    # 2. Get or create TripList (NECESSARY FOR TEMPLATE)
    trip_list_id = f"{user.username}-favourite"
    trip_list, _ = TripList.objects.get_or_create(id=trip_list_id, defaults={
        'user': user,
        'name': f"{user.username}'s Favourite Trip"
    })

    return render(request, "page/favourite/index.html", {
        'locations': locations,
        'trip_list': trip_list  # Pass this to the template
    })


# -------------------- Helpers --------------------
def _parse_int_or_none(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _unique_preserve(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _has_cycle(edges):
    """
    Check cycle in edge list (u->v) using Kahn (topo sort).
    edges: list[tuple[int,int]]
    """
    from collections import deque, defaultdict
    indeg = defaultdict(int)
    g = defaultdict(list)
    nodes = set()
    for u, v in edges:
        g[u].append(v)
        indeg[v] += 1
        nodes.add(u); nodes.add(v)
    dq = deque([n for n in nodes if indeg[n] == 0])
    cnt = 0
    while dq:
        n = dq.popleft()
        cnt += 1
        for w in g[n]:
            indeg[w] -= 1
            if indeg[w] == 0:
                dq.append(w)
    return cnt < len(nodes)


# -------------------- Create Trip --------------------
@login_required
@transaction.atomic
def create_trip(request):
    """
    Create TripPath from Favourite form (new HTML).
    - Save `locations_ordered` (JSON list of IDs in order) to display correct order.
    - Attach M2M `trip.locations` for convenience in reports/queries (M2M DOES NOT preserve order).
    - Validate start/end ∈ selected set; validate precedence cycle server-side.
    """
    if request.method != 'POST':
        return redirect('favourite')

    user = request.user
    trip_list_id = f"{user.username}-favourite"
    trip_list, _ = TripList.objects.get_or_create(
        id=trip_list_id,
        defaults={'user': user, 'name': f"{user.username}'s Favourite Trip"}
    )

    # --- Get & validate basic data ---
    path_name = (request.POST.get('path_name') or '').strip()
    if not path_name:
        messages.error(request, "Please enter a trip name.")
        return redirect('favourite')

    raw_ids = request.POST.getlist('locations')
    try:
        selected_ids = _unique_preserve([int(x) for x in raw_ids])
    except ValueError:
        messages.error(request, "Invalid location data.")
        return redirect('favourite')

    if not selected_ids:
        messages.error(request, "Please select at least one location.")
        return redirect('favourite')

    # Get favourite locations of user, PRESERVE ORDER according to selected_ids
    when_list = [When(id=pk, then=pos) for pos, pk in enumerate(selected_ids)]
    preserved = Case(*when_list, default=Value(len(when_list)), output_field=IntegerField())
    locations = list(
        Location.objects.filter(id__in=selected_ids, favourited_by=user).order_by(preserved)
    )

    if len(locations) != len(selected_ids):
        messages.error(request, "Some selected locations are no longer in your favourites.")
        return redirect('favourite')

    id_to_index = {loc.id: idx for idx, loc in enumerate(locations)}
    index_to_id = {idx: loc.id for idx, loc in enumerate(locations)}
    coordinates = [loc.coordinate for loc in locations]

    # --- Start/End ---
    start_id = _parse_int_or_none(request.POST.get('start_point'))
    end_id   = _parse_int_or_none(request.POST.get('end_point'))

    if start_id and start_id not in id_to_index:
        messages.error(request, "Invalid start point.")
        return redirect('favourite')
    if end_id and end_id not in id_to_index:
        messages.error(request, "Invalid end point.")
        return redirect('favourite')

    # --- Pinned / Precedence ---
    pinned_positions = [None] * len(locations)      
    fixed_position_flags = [False] * len(locations)
    precedence_constraints = []

    for loc in locations:
        loc_id = loc.id
        idx = id_to_index[loc_id]

        # Pin
        pinned_str = request.POST.get(f'pinned_order_{loc_id}')
        if pinned_str and pinned_str.isdigit():
            pinned_index = int(pinned_str) - 1
            if 0 <= pinned_index < len(locations):
                pinned_positions[pinned_index] = idx
                fixed_position_flags[pinned_index] = True

        # Precedence (must go after)
        after_id_str = request.POST.get(f'precedence_after_{loc_id}')
        if after_id_str and after_id_str.isdigit():
            after_id = int(after_id_str)
            if after_id in id_to_index:
                precedence_constraints.append((id_to_index[after_id], idx))

    # Check precedence cycle on server
    if _has_cycle(precedence_constraints):
        messages.error(request, "Cycle detected in 'must go after' constraints. Please review.")
        return redirect('favourite')

    # --- Build graph weights ---
    durations_map = {}
    graph = Graph(len(locations))
    for i in range(len(coordinates)):
        for j in range(len(coordinates)):
            if i == j:
                continue
            dist, duration = distance(coordinates[i], coordinates[j])
            graph.add_edge(i, j, dist)
            durations_map[(i, j)] = duration

    start_index = id_to_index.get(start_id) if start_id is not None else None
    end_index   = id_to_index.get(end_id)   if end_id   is not None else None

    # --- Solve path ---
    try:
        path, cost = graph.find_hamiltonian_path(
            fixed_position=fixed_position_flags,
            precedence_constraints=precedence_constraints,
            start=start_index,
            end=end_index
        )
    except Exception as e:
        messages.error(request, f"An error occurred while creating the trip: {e}")
        return redirect('favourite')

    if not path:
        messages.error(request, "Unable to generate a valid trip with the selected constraints.")
        return redirect('favourite')

    total_duration = sum(durations_map.get((path[i], path[i+1]), 0) for i in range(len(path) - 1))
    ordered_location_ids = [index_to_id[i] for i in path]

    # --- Save TripPath ---
    trip = TripPath.objects.create(
        trip_list=trip_list,
        path_name=path_name,
        locations_ordered=json.dumps(ordered_location_ids),
        total_distance=cost,
        total_duration=total_duration,
        start_point_id=start_id if start_id is not None else None,
        end_point_id=end_id if end_id is not None else None,
    )

    # Attach M2M (order not preserved; order loaded from locations_ordered)
    trip.locations.set(locations)

    # Remove favourites
    for loc in locations:
        loc.favourited_by.remove(user)

    messages.success(request, "Trip created successfully.")
    return redirect('trip')


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
