from django.urls import path
from . import views
from . import firebase_views
from django.conf import settings
from django.conf.urls.static import static
app_name = 'map_app'

urlpatterns = [
    # path("", views.maps, name="maps"),
    path("maps_search", views.maps_search, name="maps_search"),
    path("show_towers/", views.show_towers, name="show_towers"),
    path('get-towers/', views.get_towers,
         name='get_towers_in_bbox'),
    #     path('get-towers/', views.get_towers_in_bbox,
    #          name='get_towers_in_bbox'),
    path('send-message/', views.send_message, name='send_message'),
    path('geojson-map/', views.geojson_map, name='geojson_map'),
    path("firebase-config/", views.firebase_config, name="firebase_config"),
    path('add-users/', firebase_views.add_users_to_towers,
         name='add_users_to_towers'),
    path('view-messages/', views.view_messages, name='view_messages'),
    path('send-message/', firebase_views.send_message, name='send_message'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
