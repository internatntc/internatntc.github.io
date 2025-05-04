from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Role, UserRole, Service

User = get_user_model()


class UserRoleInline(admin.StackedInline):
    model = UserRole
    can_delete = False
    verbose_name_plural = 'Role Assignment'


class UserAdmin(BaseUserAdmin):
    inlines = (UserRoleInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role')

    def get_role(self, obj):
        return obj.role_assignment.role.name if hasattr(obj, 'role_assignment') else None
    get_role.short_description = 'Role'


# Only unregister if User is already registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(Service)
