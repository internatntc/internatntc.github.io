from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from rbac.models import UserRole


def has_role_access(view_name):
    """
    Decorator to check if user's role has access to the specified view/service.
    Now properly implements:
    - Higher roles inherit all services from roles below them
    - Lower roles only have explicitly assigned services
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login_view')

            try:
                user_role = request.user.role_assignment.role
            except AttributeError:
                return HttpResponseForbidden("You don't have any role assigned.")

            # Check if the role has this service directly
            if user_role.services.filter(view_name=view_name).exists():
                return view_func(request, *args, **kwargs)

            # Check child roles (lower in hierarchy)
            # Higher roles should inherit services from lower roles
            roles_to_check = user_role.children.all()
            while roles_to_check:
                current_role = roles_to_check.pop()
                if current_role.services.filter(view_name=view_name).exists():
                    return view_func(request, *args, **kwargs)
                # Add this role's children to be checked
                roles_to_check.extend(current_role.children.all())

            return HttpResponseForbidden("You don't have permission to access this page.")

        return _wrapped_view
    return decorator


def role_required(role_name):
    """
    Decorator to check if user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login_view')

            try:
                user_role = request.user.role_assignment.role.name
            except AttributeError:
                return HttpResponseForbidden("You don't have any role assigned.")

            if user_role == role_name:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(f"You need {role_name} role to access this page.")

        return _wrapped_view
    return decorator


def hierarchy_required(levels):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                user_role = request.user.role_assignment.role
            except UserRole.DoesNotExist:
                return HttpResponseForbidden("No role assigned.")

            # ✅ Check if the role's level is in the allowed list
            if user_role.hierarchy_level in levels:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden("You don't have permission.")
        return _wrapped_view
    return decorator
