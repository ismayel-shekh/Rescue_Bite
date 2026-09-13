from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from accounts.models import User
from food.models import FoodListing
from impact.services import get_platform_impact
from reservations.models import Reservation
from restaurants.models import Restaurant


def staff_required(view_func):
    @wraps(view_func)
    @user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="accounts:login",
    )
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapped


@staff_required
def dashboard(request):
    active_listings = FoodListing.objects.filter(
        status=FoodListing.Status.ACTIVE,
        quantity__gt=0,
    ).select_related("restaurant")
    recent_reservations = Reservation.objects.select_related(
        "customer",
        "food_listing__restaurant",
    )[:6]

    return render(
        request,
        "admin_dashboard/index.html",
        {
            "metrics": {
                "customers": User.objects.filter(role=User.Role.CUSTOMER).count(),
                "owners": User.objects.filter(role=User.Role.RESTAURANT_OWNER).count(),
                "restaurants": Restaurant.objects.count(),
                "active_listings": active_listings.count(),
                "reservations": Reservation.objects.count(),
                "collected": Reservation.objects.filter(status=Reservation.Status.COLLECTED).count(),
            },
            "impact": get_platform_impact(),
            "recent_listings": active_listings[:6],
            "recent_reservations": recent_reservations,
        },
    )
