from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    middle_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


class Service(models.Model):
    """Represents a function/view that can be accessed"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # e.g., 'map_app:show_towers'
    view_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """Represents a role in the hierarchy"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    hierarchy_level = models.PositiveIntegerField(unique=True)  # 1 is highest
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    services = models.ManyToManyField(
        Service, blank=True, related_name='roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['hierarchy_level']

    def __str__(self):
        return f"{self.name} (Level {self.hierarchy_level})"

    def clean(self):
        # Ensure hierarchy_level is unique
        if Role.objects.filter(hierarchy_level=self.hierarchy_level).exclude(pk=self.pk).exists():
            raise ValidationError(
                f"A role with hierarchy level {self.hierarchy_level} already exists.")

        # Validate parent hierarchy
        if self.parent and self.parent.hierarchy_level <= self.hierarchy_level:
            raise ValidationError(
                "Parent role must have a higher hierarchy level (lower number) than child.")


class UserRole(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_assignment'
    )
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('ROLE_CREATE', 'Role Created'),
        ('ROLE_UPDATE', 'Role Updated'),
        ('SERVICE_ASSIGN', 'Service Assigned'),
        ('USER_CREATE', 'User Created'),
        ('USER_ROLE_ASSIGN', 'User Role Assigned'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='targeted_activities')
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.timestamp}"
