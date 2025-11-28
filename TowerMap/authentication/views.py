# /app/TowerMap/authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
from rbac.models import Role, UserRole, Service
from rbac.decorators import role_required
from rbac.utils import log_activity


def login_view(request):
    """
    Handle user login with comprehensive error handling and activity logging
    """
    # If user is already authenticated, redirect to appropriate page
    if request.user.is_authenticated:
        return _redirect_based_on_role(request)
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        # Basic input validation
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, "authentication/login.html")
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Log successful login
                log_activity(
                    request=request,
                    action='LOGIN_SUCCESS',
                    details=f"User {username} logged in successfully"
                )
                
                messages.success(request, f"Welcome back, {username}!")
                return _redirect_based_on_role(request)
                
            else:
                # Log attempt to login to inactive account
                log_activity(
                    request=request,
                    action='LOGIN_INACTIVE',
                    details=f"Attempted login to inactive account: {username}"
                )
                messages.error(request, "This account is inactive. Please contact administrator.")
        else:
            # Log failed login attempt
            log_activity(
                request=request,
                action='LOGIN_FAILED',
                details=f"Failed login attempt for username: {username}"
            )
            # Don't reveal whether username exists for security
            messages.error(request, "Invalid username or password.")
    
    return render(request, "authentication/login.html")


def _redirect_based_on_role(request):
    """
    Determine redirect URL based on user's role hierarchy
    """
    user = request.user
    
    try:
        user_role = user.role_assignment.role
        
        # Redirect based on role hierarchy (highest privilege first)
        role_redirects = {
            10: "rbac:admin_dashboard",  # Super Admin
            9: "rbac:admin_dashboard",   # Admin
            8: "map_app:show_towers",    # Manager
            # Add more role levels as needed
        }
        
        # Get the redirect URL or default to towers view
        redirect_name = role_redirects.get(user_role.hierarchy_level, "map_app:show_towers")
        return redirect(redirect_name)
        
    except (AttributeError, UserRole.DoesNotExist):
        # User has no role assigned - redirect to a safe page instead of login
        log_activity(
            request=request,
            action='LOGIN_NO_ROLE',
            details=f"User {user.username} logged in but has no role assigned"
        )
        messages.warning(
            request, "You don't have any role assigned. Please contact administrator."
        )
        # Redirect to a safe default page instead of login to avoid infinite loop
        return redirect("map_app:show_towers")  # Or create a "no_role" page


def logout_view(request):
    """
    Handle user logout with activity logging
    """
    if request.user.is_authenticated:
        # Log logout activity before actually logging out
        log_activity(
            request=request,
            action='LOGOUT',
            details=f"User {request.user.username} logged out"
        )
    
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect("authentication:login_view")


@login_required
@role_required('Admin')
def dashboard(request):
    """
    Admin dashboard with user and role management
    """
    try:
        users = User.objects.select_related('role_assignment__role').all()
        roles = Role.objects.all().order_by('hierarchy_level')
        
        # Get statistics for dashboard
        total_users = users.count()
        users_with_roles = users.filter(role_assignment__isnull=False).count()
        available_roles = roles.count()
        
        context = {
            "users": users,
            "roles": roles,
            "stats": {
                "total_users": total_users,
                "users_with_roles": users_with_roles,
                "available_roles": available_roles,
            }
        }
        
        return render(request, "authentication/dashboard.html", context)
        
    except Exception as e:
        log_activity(
            request=request,
            action='DASHBOARD_ERROR',
            details=f"Error loading dashboard: {str(e)}"
        )
        messages.error(request, "Error loading dashboard. Please try again.")
        return redirect("authentication:login_view")


@login_required
@role_required('Super Admin')
def create_user(request):
    """
    Create new user with role assignment (Super Admin only)
    """
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        role_id = request.POST.get("role")
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        # Validation
        errors = []
        
        if not username:
            errors.append("Username is required.")
        
        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                with transaction.atomic():
                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=email,
                        first_name=first_name,
                        last_name=last_name
                    )

                    # Assign role if provided
                    role = None
                    if role_id:
                        role = Role.objects.get(id=role_id)
                        UserRole.objects.create(user=user, role=role)
                    
                    # Log user creation
                    log_activity(
                        request=request,
                        action='USER_CREATED',
                        target_user=user,
                        details=f"Created user {username} with role {role.name if role else 'No role'}"
                    )

                    messages.success(request, f"User {username} created successfully.")
                    return redirect("authentication:dashboard")
                    
            except Role.DoesNotExist:
                messages.error(request, "Selected role does not exist.")
            except Exception as e:
                log_activity(
                    request=request,
                    action='USER_CREATION_ERROR',
                    details=f"Error creating user {username}: {str(e)}"
                )
                messages.error(request, f"Error creating user: {str(e)}")

    # GET request - show form
    roles = Role.objects.all().order_by('hierarchy_level')
    return render(request, "authentication/create_user.html", {
        "roles": roles,
        "min_password_length": 8
    })


@login_required
def profile_view(request):
    """
    Allow users to view and update their own profile
    """
    user = request.user
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        
        # Update user profile
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        log_activity(
            request=request,
            action='PROFILE_UPDATED',
            details="Updated profile information"
        )
        
        messages.success(request, "Profile updated successfully.")
        return redirect("authentication:profile")
    
    # Get user's role information
    try:
        user_role = user.role_assignment.role
        role_name = user_role.name
    except (AttributeError, UserRole.DoesNotExist):
        role_name = "No role assigned"
    
    context = {
        "user": user,
        "role_name": role_name
    }
    
    return render(request, "authentication/profile.html", context)
