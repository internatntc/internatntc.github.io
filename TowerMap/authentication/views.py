from rbac.utils import log_activity
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from rbac.models import Role, UserRole, Service
from rbac.decorators import role_required


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Log the successful login
            log_activity(
                request,
                'LOGIN',
                target_user=user,
                details=f"User {username} logged in successfully"
            )

            try:
                # Redirect based on role hierarchy (highest role first)
                if user.role_assignment.role.hierarchy_level == 10:
                    return redirect("rbac:admin_dashboard")
                return redirect("map_app:show_towers")
            except AttributeError:
                # User has no role assigned
                log_activity(
                    request,
                    'LOGIN',
                    target_user=user,
                    details=f"User {username} logged in but has no role assigned"
                )
                messages.warning(
                    request, "You don't have any role assigned. Contact administrator.")
                return redirect("authentication:login_view")
        else:
            # Log failed login attempt
            log_activity(
                request,
                'LOGIN',
                details=f"Failed login attempt for username: {username}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.error(request, "Invalid username or password.")

    return render(request, "authentication/login.html")


def logout_view(request):
    logout(request)
    return redirect("authentication:login_view")


@login_required
@role_required('Admin')
def dashboard(request):
    users = User.objects.all()
    roles = Role.objects.all().order_by('hierarchy_level')
    return render(request, "authentication/dashboard.html", {
        "users": users,
        "roles": roles
    })


@login_required
@role_required('Super Admin')
def create_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role_id = request.POST.get("role")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                password=password
            )

            if role_id:
                role = Role.objects.get(id=role_id)
                UserRole.objects.create(user=user, role=role)

            messages.success(request, f"User {username} created successfully.")
            return redirect("authentication:dashboard")

    roles = Role.objects.all().order_by('hierarchy_level')
    return render(request, "authentication/create_user.html", {"roles": roles})
