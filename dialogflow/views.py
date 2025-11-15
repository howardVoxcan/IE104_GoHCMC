from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from location.models import Location
from .models import TemporaryTripCart, TemporaryUser
from favourite.models import TripPath, TripList
from favourite.TSP import Graph, distance
import json, traceback, logging
from urllib.parse import urlencode

# Create your views here.
logger = logging.getLogger(__name__)

def extract_session_id(data, parameters):
    session_full = data.get('session', '')
    session_id = session_full.split('/')[-1] if session_full else None

    if not session_id and 'originalDetectIntentRequest' in data:
        session_id = data['originalDetectIntentRequest'].get('payload', {}).get('sessionId')

    if not session_id:
        session_id = parameters.get('session_id')

    return session_id

def normalize_locations(loc):
    if loc is None:
        return []
    if isinstance(loc, str):
        return [loc]
    if isinstance(loc, list):
        return loc
    return [str(loc)]

def get_or_create_temp_user(session_id):
    temp_user, _ = TemporaryUser.objects.get_or_create(session_id=session_id)
    return temp_user

def get_or_create_temp_cart(session_id, user=None):
    cart, created = TemporaryTripCart.objects.get_or_create(session_id=session_id, defaults={"user": user})
    if not created and cart.user is None and user is not None:
        cart.user = user
        cart.save()
    return cart

@csrf_exempt
def dialogflow_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        print(request.body)
        data = json.loads(request.body.decode("utf-8"))
        intent_name = data['queryResult']['intent']['displayName']
        parameters  = data['queryResult'].get('parameters', {})

        # Extract session and user
        session_id = extract_session_id(data, parameters)
        user_id    = data.get('originalDetectIntentRequest', {}) \
                         .get('payload', {}) \
                         .get('userId') or parameters.get('user_id')

        user = None
        if user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

        result = handle_intent(request, intent_name, parameters, user, session_id)

        if result is True:
            return JsonResponse({"fulfillmentText": data['queryResult'].get('fulfillmentText', "Done.")})
        elif isinstance(result, str):
            return JsonResponse({"fulfillmentText": result})
        else:
            return JsonResponse({"fulfillmentText": "Unhandled case."})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "fulfillmentText": "An error occurred while processing your request.",
            "debug": str(e)
        })

def handle_intent(request, intent_name, parameters, user=None, session_id=None):
    if not session_id:
        try:
            data = json.loads(request.body.decode("utf-8"))
            session_id = extract_session_id(data, parameters)
        except:
            pass
    if not session_id:
        return "Missing session ID."

    if user is None:
        user = get_or_create_temp_user(session_id)

    try:
        trip_cart_obj = get_or_create_temp_cart(session_id, user)
    except Exception as e:
        return "Could not create or access your trip session."

    locations_list = normalize_locations(parameters.get("locations") or [])

    if intent_name in ["Default Welcome Intent", "Default Fallback Intent", "discovering.ability"]:
        return True

    elif intent_name == "add.location":
        if not user or isinstance(user, TemporaryUser):
            return "Please log in to add favourites."
        if not locations_list:
            return "Please specify a location to add."
        for loc in locations_list:
            try:
                location_obj = Location.objects.get(location__iexact=loc)
                location_obj.favourited_by.add(user)
            except Location.DoesNotExist:
                return f"Location '{loc}' does not exist."
        return True

    elif intent_name == "remove.location":
        if not user or isinstance(user, TemporaryUser):
            return "Please log in to remove favourites."
        if not locations_list:
            return "Please specify a location to remove."
        for loc in locations_list:
            try:
                location_obj = Location.objects.get(location__iexact=loc)
                location_obj.favourited_by.remove(user)
            except Location.DoesNotExist:
                return f"Location '{loc}' does not exist."
        return True

    elif intent_name == "start.trip":
        trip_cart_obj.locations = []
        trip_cart_obj.start_location = None
        trip_cart_obj.end_location = None
        trip_cart_obj.save()
        return True

    elif intent_name == "set.start.location":
        if locations_list:
            trip_cart_obj.start_location = locations_list[0]
            trip_cart_obj.save()
            return True
        return "Please tell me which location to set as the starting point."

    elif intent_name == "set.end.location":
        if locations_list:
            trip_cart_obj.end_location = locations_list[0]
            trip_cart_obj.save()
            return True 
        return "Please tell me which location to set as the ending point."

    elif intent_name == "trip.create.add.location":
        updated = False
        for loc in locations_list:
            if loc not in trip_cart_obj.locations:
                trip_cart_obj.locations.append(loc)
                updated = True
        if updated:
            trip_cart_obj.save()
            return True
        return "Those locations are already in your trip."

    elif intent_name == "trip.create.remove.location":
        removed, not_found = [], []
        for loc in locations_list:
            if loc in trip_cart_obj.locations:
                trip_cart_obj.locations.remove(loc)
                removed.append(loc)
            else:
                not_found.append(loc)
        trip_cart_obj.save()
        if removed and not not_found:
            return f"Removed {', '.join(removed)} from your trip."
        if removed and not_found:
            return f"Removed {', '.join(removed)}. However, {', '.join(not_found)} were not in your trip list."
        return f"{', '.join(not_found)} is/are not in your trip list."

    elif intent_name == "trip.create.complete":
        locations = trip_cart_obj.locations or []
        start_name = trip_cart_obj.start_location
        end_name = trip_cart_obj.end_location

        if not locations and not (start_name and end_name):
            return "Your trip has no locations. Please add some before finishing."

        # Normalize existing location names (lowercase) for comparison
        existing = [loc.lower() for loc in locations]

        updated = False
        # Force inclusion of start location at the beginning if missing
        if start_name and start_name.lower() not in existing:
            locations.insert(0, start_name)
            updated = True

        # Update existing after possible start insertion
        existing = [loc.lower() for loc in locations]

        # Force inclusion of end location at the end if missing
        if end_name and end_name.lower() not in existing:
            locations.append(end_name)
            updated = True

        # Save updated locations back to trip_cart_obj if changed
        if updated:
            trip_cart_obj.locations = locations
            trip_cart_obj.save()

        locations = trip_cart_obj.locations

        middles = [loc for loc in locations if loc not in (start_name, end_name)]

        ordered_names = []
        if start_name:
            ordered_names.append(start_name)
        ordered_names.extend(middles)
        if end_name:
            ordered_names.append(end_name)

        loc_objs = list(Location.objects.filter(location__in=ordered_names))
        found = {l.location for l in loc_objs}
        missing = [n for n in ordered_names if n not in found]
        if missing:
            logger.warning(f"[DEBUG] Missing from DB: {missing}")
        else:
            logger.debug("[DEBUG] All names found in DB.")

        name2obj = {l.location: l for l in loc_objs}
        location_list = [name2obj[n] for n in ordered_names if n in name2obj]
        final_names = [loc.location for loc in location_list]
        logger.debug(f"[DEBUG] location_list used: {final_names}")

        coords = [loc.coordinate for loc in location_list]
        index_to_id = {i: location_list[i].id for i in range(len(location_list))}
        distances, durations = [], {}
        for i in range(len(coords)):
            for j in range(len(coords)):
                if i == j: continue
                d, t = distance(coords[i], coords[j])
                distances.append((i, j, d))
                durations[(i, j)] = t

        graph = Graph(len(location_list))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        start_idx = 0
        end_idx = (len(ordered_names) - 1) if end_name else start_idx
        logger.debug(f"[DEBUG] start_idx={start_idx}, end_idx={end_idx}")

        best_path, total_dist = graph.find_hamiltonian_path(
            fixed_position=None,
            precedence_constraints=None,
            start=start_idx,
            end=end_idx
        )
        if not best_path:
            logger.error("[DEBUG] No valid path found.")
            return "Unable to generate a valid trip with the selected start/end points."

        if best_path[0] == best_path[-1]:
            best_path = best_path[:-1]
        logger.debug(f"[DEBUG] best_path indices: {best_path}")

        total_time = sum(
            durations.get((best_path[i], best_path[i+1]), 0)
            for i in range(len(best_path)-1)
        )

        itinerary_names = [location_list[i].location for i in best_path]
        logger.debug(f"[DEBUG] itinerary: {itinerary_names}")

        header = [
            f"Total distance: {total_dist:.1f} km",
            f"Total duration: {total_time:.1f} minutes",
            ""
        ]
        reply = "\n".join(header + itinerary_names)

        trip_list, _ = TripList.objects.get_or_create(user=user)
        middle_ids = [index_to_id[i] for i in best_path[1:-1]]

        trip_path = TripPath.objects.create(
            trip_list=trip_list,
            total_duration=total_time,
            total_distance=total_dist,
            locations_ordered=json.dumps(middle_ids),
            path_name=f"{user.username} chatbot TripPath",
            start_point=location_list[best_path[0]],
            end_point=location_list[best_path[-1]]
        )
        trip_path.locations.add(*[location_list[i] for i in best_path])
        trip_path.save()

        url = reverse('my_trip') + "?" + urlencode({'id': trip_list.id})
        return "Your trip has been created successfully!"

    return False