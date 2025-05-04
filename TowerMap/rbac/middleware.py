import logging
from django.contrib.auth import get_user_model
from .models import ActivityLog
from django.http import HttpResponseForbidden
from django.urls import resolve
from rbac.models import Service, Role


class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for admin and auth views
        if request.path.startswith('/admin/') or request.path.startswith('/auth/'):
            return None

        # Skip for unauthenticated users (they'll be redirected by login_required)
        if not request.user.is_authenticated:
            return None

        try:
            resolved = resolve(request.path_info)
            view_name = resolved.view_name
        except:
            return None

        # Check if this is a protected service
        try:
            service = Service.objects.get(view_name=view_name)
        except Service.DoesNotExist:
            return None

        # Check user's role access
        try:
            user_role = request.user.role_assignment.role
        except AttributeError:
            return HttpResponseForbidden("You don't have any role assigned.")

        # Check if the role has this service directly
        if user_role.services.filter(id=service.id).exists():
            return None

        # Check parent roles (higher in hierarchy)
        current_role = user_role
        while current_role.parent:
            current_role = current_role.parent
            if current_role.services.filter(id=service.id).exists():
                return None

        return HttpResponseForbidden("You don't have permission to access this page.")


logger = logging.getLogger(__name__)
User = get_user_model()


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip logging for certain paths
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return response

        try:
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    actor=request.user,
                    action='REQUEST',
                    model_affected='System',
                    instance_id='0',
                    details=f"{request.method} {request.path}"
                )
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")

        return response
