# from .utils import log_activity
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
from .utils import log_activity

User = get_user_model()


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
                request,
                'ROLE_CREATE',
                role=role,
                details=f"Created role {role.name} (Level {role.hierarchy_level})"
            )
            messages.success(request, f"Role {name} created successfully.")
            return redirect("rbac:admin_dashboard")
        except Exception as e:
            messages.error(request, f"Error creating role: {str(e)}")

    parents = Role.objects.all().order_by('hierarchy_level')
    return render(request, 'rbac/create_role.html', {'parents': parents})


@login_required
# Only roles with level 3 or 10 can access this view
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
                request,
                'SERVICE_ASSIGN',
                role=target_role,
                service=service,
                details=f"Assigned service {service.name} to role {target_role.name}"
            )
        return redirect('rbac:admin_dashboard')

    context = {
        'role': target_role,
        'services': users_own_services,  # ONLY services assigned to current user's role
        'assigned_service_ids': target_assigned_ids,
    }
    return render(request, 'rbac/assign_services.html', context)


@login_required
# @role_required('Super Admin')
@hierarchy_required([8, 9, 10])
def assign_user_role(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "POST":
        role_id = request.POST.get("role")
        role = Role.objects.get(id=role_id)

        UserRole.objects.update_or_create(
            user=user,
            defaults={'role': role}
        )
        log_activity(
            request,
            'USER_ROLE_ASSIGN',
            target_user=user,
            role=role,
            details=f"Assigned role {role.name} to user {user.username}"
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
    ).select_related('role_assignment__role', 'profile')

    # Apply search filter if query exists
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__phone_number__icontains=search_query) |
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


User = get_user_model()


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
                request,
                'USER_CREATE',
                target_user=user,
                role=role,
                details=f"Created user {user.username} with role {role.name}"
            )
            UserRole.objects.create(user=user, role=role)

            # Or wherever you want to redirect
            return redirect('rbac:user_roles_view')
    else:
        form = CreateUserForm()

    return render(request, 'rbac/create_user.html', {'form': form})


@login_required
@has_role_access('rbac:activity_logs')
# @role_required('Super Admin')
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

# Logs
# @hierarchy_required([3, 10])
# def assign_services(request, role_id):
#     target_role = get_object_or_404(Role, id=role_id)
#     current_user_role = request.user.role_assignment.role

#     if target_role.hierarchy_level <= current_user_role.hierarchy_level:
#         log_activity(
#             request,
#             action='UNAUTHORIZED',
#             model_affected='Role',
#             instance_id=role_id,
#             details=f'Tried to assign services to equal/higher role'
#         )
#         return HttpResponseForbidden("Can only assign to lower roles")

#     users_own_services = current_user_role.services.all()

#     if request.method == 'POST':
#         selected_services = users_own_services.filter(
#             id__in=request.POST.getlist('services', [])
#         )

#         # Get changes before updating
#         previous_services = set(target_role.services.all())
#         target_role.services.set(selected_services)
#         current_services = set(target_role.services.all())

#         # Calculate changes
#         added_services = current_services - previous_services
#         removed_services = previous_services - current_services

#         # Log the changes
#         if added_services:
#             log_activity(
#                 request,
#                 action='ASSIGN',
#                 model_affected='Role',
#                 instance_id=role_id,
#                 details=f'Added services: {", ".join([s.name for s in added_services])}'
#             )

#         if removed_services:
#             log_activity(
#                 request,
#                 action='REVOKE',
#                 model_affected='Role',
#                 instance_id=role_id,
#                 details=f'Removed services: {", ".join([s.name for s in removed_services])}'
#             )

#         return redirect('rbac:admin_dashboard')
