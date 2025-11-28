# /app/TowerMap/rbac/views.py
from django.db.models import Q
from .models import ActivityLog
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden
from .forms import CreateUserForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Role, Service, UserRole
from .decorators import has_role_access, role_required, hierarchy_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

# Ensure User model is consistently obtained
User = get_user_model()


# --- Utility Functions (These were likely in rbac/utils.py but are fine here too) ---

def log_activity(request=None, user=None, action="", details="", ip_address=None, **kwargs):
    """
    Universal activity logging function
    Supports both request-based and user-based calls
    """
    try:
        # Determine the user - priority: explicit user > request user
        activity_user = user
        if activity_user is None and request and hasattr(request, 'user') and request.user.is_authenticated:
            activity_user = request.user
        
        # Get IP address from request if available
        if ip_address is None and request:
            ip_address = get_client_ip(request)
        
        # Extract additional context from kwargs
        target_user = kwargs.get('target_user')
        role = kwargs.get('role')
        service = kwargs.get('service')
        
        # Create the activity log
        activity_log = ActivityLog(
            user=activity_user,
            action=action,
            details=details,
            ip_address=ip_address
        )
        
        # Set optional foreign keys if provided
        if target_user:
            activity_log.target_user = target_user
        if role:
            activity_log.role = role
        if service:
            activity_log.service = service
            
        activity_log.save()
        return True
        
    except Exception as e:
        # In a real application, you'd log this to an error reporting tool, not just print
        print(f"Activity logging failed: {e}")
        return False

def get_client_ip(request):
    """Get the client's IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# --- View Functions ---

@login_required
@hierarchy_required([8, 9, 10])
def admin_dashboard(request):
    roles = Role.objects.all().order_by('hierarchy_level')
    try:
        # Get services assigned to current user's role
        current_user_services = request.user.role_assignment.role.services.all()
    except UserRole.DoesNotExist:
        current_user_services = Service.objects.none()
    users = User.objects.filter(
        role_assignment__isnull=False).select_related('role_assignment__role')
    return render(request, 'rbac/admin_dashboard.html', {
        'roles': roles,
        'services': current_user_services,
        'users': users
    })


@login_required
@hierarchy_required([9, 10])
def create_role(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        hierarchy_level = request.POST.get("hierarchy_level")
        parent_id = request.POST.get("parent")

        try:
            parent = Role.objects.get(id=parent_id) if parent_id else None
            role = Role.objects.create(
                name=name,
                description=description,
                hierarchy_level=hierarchy_level,
                parent=parent
            )
            log_activity(
                request=request,
                action='ROLE_CREATE',
                details=f"Created role {role.name} (Level {role.hierarchy_level})",
                role=role
            )
            messages.success(request, f"Role {name} created successfully.")
            return redirect("rbac:admin_dashboard")
        except Exception as e:
            messages.error(request, f"Error creating role: {str(e)}")

    parents = Role.objects.all().order_by('hierarchy_level')
    return render(request, 'rbac/create_role.html', {'parents': parents})


@login_required
@hierarchy_required([8, 9, 10])
def assign_services(request, role_id):
    target_role = get_object_or_404(Role, id=role_id)

    # Get current user's role and their assigned services
    try:
        current_user_role = request.user.role_assignment.role
        # This gets ONLY the services assigned to current user's role
        users_own_services = current_user_role.services.all()
    except UserRole.DoesNotExist:
        return HttpResponseForbidden("You don't have a role assigned.")

    # Hierarchy check - can only assign to roles below current user's level
    if target_role.hierarchy_level >= current_user_role.hierarchy_level:
        return HttpResponseForbidden("You can only assign to roles below your level.")

    # Get which of current user's services are assigned to target role
    target_assigned_ids = target_role.services.filter(
        id__in=users_own_services.values('id')
    ).values_list('id', flat=True)

    if request.method == 'POST':
        # Filter to only include services from current user's assigned services
        selected_services = users_own_services.filter(
            id__in=request.POST.getlist('services', [])
        )
        target_role.services.set(selected_services)
        for service in selected_services:
            log_activity(
                request=request,
                action='SERVICE_ASSIGN',
                details=f"Assigned service {service.name} to role {target_role.name}",
                role=target_role,
                service=service
            )
        messages.success(request, f"Services assigned to role {target_role.name} successfully.")
        return redirect('rbac:admin_dashboard')

    context = {
        'role': target_role,
        'services': users_own_services,  # ONLY services assigned to current user's role
        'assigned_service_ids': target_assigned_ids,
    }
    return render(request, 'rbac/assign_services.html', context)


@login_required
@hierarchy_required([8, 9, 10])
def assign_user_role(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        role_id = request.POST.get("role")
        role = get_object_or_404(Role, id=role_id)

        UserRole.objects.update_or_create(
            user=user,
            defaults={'role': role}
        )
        log_activity(
            request=request,
            action='USER_ROLE_ASSIGN',
            details=f"Assigned role {role.name} to user {user.username}",
            target_user=user,
            role=role
        )
        messages.success(
            request, f"Role {role.name} assigned to {user.username}.")
        return redirect("rbac:admin_dashboard")

    roles = Role.objects.all().order_by('hierarchy_level')
    try:
        current_role = user.role_assignment.role
    except AttributeError:
        current_role = None

    return render(request, 'rbac/assign_user_role.html', {
        'user': user,
        'roles': roles,
        'current_role': current_role
    })


@login_required
@role_required('Super Admin')
def user_roles_view(request):
    roles = Role.objects.all().order_by('hierarchy_level')
    selected_role_id = request.GET.get(
        'role', roles.first().id if roles.exists() else None)
    search_query = request.GET.get('search', '').strip()

    # Get the selected role
    selected_role = get_object_or_404(Role, id=selected_role_id)

    # Start with all users in the selected role
    users = User.objects.filter(
        role_assignment__role=selected_role
    ).select_related('role_assignment__role') # Removed 'profile' related fetch as it might not be mandatory

    # Apply search filter if query exists
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        ).distinct()

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'roles': roles,
        'selected_role': selected_role,
        'page_obj': page_obj,
    }
    return render(request, 'rbac/user_roles_tabs.html', context)


@role_required('Super Admin')
def create_user_view(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.save()

            role = form.cleaned_data['role']
            log_activity(
                request=request,
                action='USER_CREATE',
                details=f"Created user {user.username} with role {role.name}",
                target_user=user,
                role=role
            )
            UserRole.objects.create(user=user, role=role)

            messages.success(request, f"User {user.username} created successfully and assigned role {role.name}.")
            return redirect('rbac:user_roles_view')
    else:
        form = CreateUserForm()

    return render(request, 'rbac/create_user.html', {'form': form})


@login_required
@has_role_access('rbac:activity_logs')
def activity_logs(request):
    tab = request.GET.get('tab', 'all')
    logs = ActivityLog.objects.all().select_related(
        'user', 'target_user', 'role', 'service'
    ).order_by('-timestamp')

    if tab == 'logins':
        logs = logs.filter(action='LOGIN')
    elif tab == 'role_creations':
        logs = logs.filter(action__in=['ROLE_CREATE', 'ROLE_UPDATE'])
    elif tab == 'service_assignments':
        logs = logs.filter(action='SERVICE_ASSIGN')
    elif tab == 'user_creations':
        logs = logs.filter(action='USER_CREATE')
    elif tab == 'role_assignments':
        logs = logs.filter(action='USER_ROLE_ASSIGN')

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_tab': tab,
        'tabs': [
            ('all', 'All Activities'),
            ('logins', 'User Logins'),
            ('role_creations', 'Role Creations/Updates'),
            ('service_assignments', 'Service Assignments'),
            ('user_creations', 'User Creations'),
            ('role_assignments', 'Role Assignments'),
        ]
    }
    return render(request, 'rbac/activity_logs.html', context)
