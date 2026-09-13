from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.views import role_required
from impact.services import get_customer_impact

from .models import Notification


@role_required(User.Role.CUSTOMER)
def index(request):
    notifications = Notification.objects.for_customer(request.user)
    return render(
        request,
        "notifications/index.html",
        {"notifications": notifications, "impact": get_customer_impact(request.user)},
    )


@role_required(User.Role.CUSTOMER)
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, customer=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    messages.success(request, "Notification marked as read.")
    return redirect("notifications:index")
