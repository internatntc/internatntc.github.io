# authentication/views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
User = get_user_model()

# Check if user is admin


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("authentication:dashboard")
            return redirect("map_app:show_towers")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "authentication/login.html")


def logout_view(request):
    logout(request)
    return redirect("authentication:login_view")


@login_required(login_url="authentication:login_view")
@user_passes_test(is_admin, login_url="map_app:show_towers")
def dashboard(request):
    users = User.objects.all()  # Fetch all users for management
    return render(request, "authentication/dashboard.html", {"users": users})


@login_required(login_url="authentication:login_view")
@user_passes_test(is_admin, login_url="map_app:show_towers")
def create_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Checkbox returns "on" if checked
        is_admin = request.POST.get("is_admin") == "on"

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_superuser=is_admin,  # Admin status
                is_staff=is_admin       # Required for admin access
            )
            user.save()
            messages.success(request, f"User {username} created successfully.")
            return redirect("authentication:dashboard")

    return render(request, "authentication/create_user.html")
