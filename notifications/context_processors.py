from .models import Notification


def notification_summary(request):
    if not request.user.is_authenticated or getattr(request.user, "role", None) != "CUSTOMER":
        return {"unread_notification_count": 0, "recent_notifications": []}
    return {
        "unread_notification_count": Notification.objects.unread_for(request.user).count(),
        "recent_notifications": Notification.objects.for_customer(request.user)[:5],
    }
