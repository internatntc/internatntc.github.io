from shapely.geometry import Point, Polygon
from django.views.decorators.http import require_GET
from rbac.models import UserRole
from .firebase_views import get_message_groups  # Adjust import if in views.py
from django.http import JsonResponse
import json
import os
from django.conf import settings
from django.shortcuts import render
from .models import Tower, UserCell
from django.views.decorators.csrf import csrf_exempt
from firebase_admin import db
from django.contrib.auth.decorators import login_required
from rbac.decorators import has_role_access


@login_required(login_url='authentication:login_view')
@has_role_access('map_app:show_towers')
def show_towers(request):
    message_groups = get_message_groups()
    return render(request, 'map_app/show_towers.html', {'message_groups': message_groups})


@login_required(login_url='authentication:login_view')
@has_role_access('map_app:view_messages')
def view_messages(request):
    message_groups = get_message_groups()
    return render(request, 'map_app/view_messages.html', {'message_groups': message_groups})


@login_required(login_url='authentication:login_view')
@has_role_access('map_app:geojson_map')
def geojson_map(request):
    # Correct path to the static folder where your GeoJSON files are stored
    geojson_folder = os.path.join(
        settings.BASE_DIR, 'map_app', 'static', 'json')

    # List all GeoJSON files in the folder
    geojson_files = [f for f in os.listdir(
        geojson_folder) if f.endswith('.geojson')]

    return render(request, 'map_app/map.html', {'geojson_files': geojson_files})


@has_role_access('map_app:maps')
def maps(request):
    return render(request, 'map_app/maps.html')


@has_role_access('map_app:maps_search')
def maps_search(request):
    return render(request, 'map_app/maps_search.html')


@login_required(login_url='authentication:login_view')
@has_role_access('map_app:get_towers')
def get_towers(request):
    towers = Tower.objects.all()
    tower_data = [
        {
            'id': tower.id,
            'name': tower.name,
            'latitude': tower.latitude,
            'longitude': tower.longitude,
        }
        for tower in towers
    ]
    return JsonResponse({'towers': tower_data})

# @require_GET
# def get_towers_in_bbox(request):
#     # Get bounding box parameters if provided
#     bbox = request.GET.get('bbox')

#     # Initialize queryset
#     towers = Tower.objects.all()

#     # Apply bounding box filter if provided
#     if bbox:
#         try:
#             # Parse bbox as min_lon,min_lat,max_lon,max_lat
#             min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(','))

#             # Filter towers within bounding box
#             towers = towers.filter(
#                 longitude__gte=min_lon,
#                 longitude__lte=max_lon,
#                 latitude__gte=min_lat,
#                 latitude__lte=max_lat
#             )
#         except (ValueError, AttributeError):
#             # If bbox is malformed, return empty response or all towers
#             return JsonResponse({'towers': []})

#     # Prepare response data
#     tower_data = [
#         {
#             'id': tower.id,
#             'name': tower.name,
#             'latitude': tower.latitude,
#             'longitude': tower.longitude,
#         }
#         for tower in towers
#     ]

#     return JsonResponse({'towers': tower_data})



@csrf_exempt
def get_towers_in_bbox(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            polygon_coords = data.get('polygon')

            if not polygon_coords:
                return JsonResponse({'towers': []})

            # Convert to Shapely polygon (assuming first array is outer ring)
            polygon = Polygon(polygon_coords[0])

            # Get towers within polygon's bounding box first (for performance)
            min_lon, min_lat, max_lon, max_lat = polygon.bounds
            potential_towers = Tower.objects.filter(
                longitude__gte=min_lon,
                longitude__lte=max_lon,
                latitude__gte=min_lat,
                latitude__lte=max_lat
            )

            # Precise filtering
            towers_in_polygon = []
            for tower in potential_towers:
                if polygon.contains(Point(tower.longitude, tower.latitude)):
                    towers_in_polygon.append({
                        'id': tower.id,
                        'name': tower.name,
                        'latitude': tower.latitude,
                        'longitude': tower.longitude,
                    })

            return JsonResponse({'towers': towers_in_polygon})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'POST required'}, status=405)


def firebase_config(request):
    config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
    }
    return JsonResponse(config)


# Send messages

@has_role_access('map_app:send_message')
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tower_ids = data.get('tower_ids', [])
        message = data.get('message', '')

        # Get all numbers linked to selected towers
        cell_numbers = UserCell.objects.filter(
            tower_id__in=tower_ids).values_list('cell_number', flat=True)

        # Save messages in Firebase
        ref = db.reference('/messages')
        for number in cell_numbers:
            ref.child(number).push({'message': message})

        return JsonResponse({'success': True, 'sent_to': list(cell_numbers)})

    return JsonResponse({'error': 'Invalid request'}, status=400)
