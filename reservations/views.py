from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.views import role_required
from food.models import FoodListing
from impact.services import get_customer_impact

from .forms import ReservationForm
from .models import Reservation
from .services import ReservationServiceError, cancel_reservation, create_reservation, mark_collected


@role_required(User.Role.CUSTOMER)
def create(request, listing_id):
    listing = get_object_or_404(FoodListing.objects.select_related("restaurant"), pk=listing_id)
    listing.refresh_status()
    form = ReservationForm(request.POST or None, max_quantity=listing.quantity)
    if request.method == "POST" and form.is_valid():
        try:
            reservation = create_reservation(
                customer=request.user,
                listing_id=listing.pk,
                quantity=form.cleaned_data["quantity"],
            )
        except ReservationServiceError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Your reservation is confirmed.")
            return redirect("reservations:confirmation", code=reservation.reservation_code)
    return render(request, "reservations/create.html", {"listing": listing, "form": form})


@role_required(User.Role.CUSTOMER)
def confirmation(request, code):
    reservation = get_object_or_404(
        Reservation.objects.select_related("food_listing__restaurant"),
        reservation_code=code,
        customer=request.user,
    )
    return render(request, "reservations/confirmation.html", {"reservation": reservation})


@role_required(User.Role.CUSTOMER)
def customer_list(request):
    reservations = Reservation.objects.filter(customer=request.user).select_related("food_listing__restaurant")
    return render(
        request,
        "reservations/customer_list.html",
        {"reservations": reservations, "impact": get_customer_impact(request.user)},
    )


@role_required(User.Role.CUSTOMER)
@require_POST
def cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, customer=request.user)
    try:
        cancel_reservation(reservation=reservation, actor=request.user)
    except ReservationServiceError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Reservation cancelled.")
    return redirect("reservations:customer_list")


@role_required(User.Role.RESTAURANT_OWNER)
@require_POST
def collect(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    try:
        mark_collected(reservation=reservation, actor=request.user)
    except ReservationServiceError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Reservation marked as collected.")
    return redirect("restaurants:reservations")
