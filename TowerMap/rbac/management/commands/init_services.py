from django.core.management.base import BaseCommand
from rbac.models import Service
from map_app import urls as map_urls
from django.urls import get_resolver

class Command(BaseCommand):
    help = 'Initialize services from URL patterns'

    def handle(self, *args, **options):
        # Get all URL patterns
        resolver = get_resolver()
        url_patterns = []
        
        # Recursively get all URL patterns
        def extract_urls(url_patterns, namespace=None):
            for pattern in url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    new_namespace = pattern.namespace if pattern.namespace else namespace
                    extract_urls(pattern.url_patterns, new_namespace)
                else:
                    name = pattern.name
                    if namespace:
                        name = f"{namespace}:{name}"
                    url_patterns.append((name, str(pattern.pattern)))
        
        extract_urls(resolver.url_patterns)
        
        # Create services for map_app views
        map_views = [
            ('Show Towers', 'map_app:show_towers'),
            ('View Messages', 'map_app:view_messages'),
            ('GeoJSON Map', 'map_app:geojson_map'),
            ('Get Towers', 'map_app:get_towers'),
            ('Send Message', 'map_app:send_message'),
        ]
        
        for name, view_name in map_views:
            Service.objects.get_or_create(
                name=name,
                view_name=view_name,
                defaults={'description': f"Access to {name} functionality"}
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized services'))