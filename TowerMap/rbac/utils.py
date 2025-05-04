from ipware import get_client_ip
from .models import ActivityLog


def log_activity(request, action, target_user=None, role=None, service=None, details=""):
    ip_address, _ = get_client_ip(request)
    ActivityLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_user=target_user,
        role=role,
        service=service,
        details=details,
        ip_address=ip_address
    )
