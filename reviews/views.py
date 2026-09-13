from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import role_required
from reservations.models import Reservation

from .forms import ReviewForm
from .models import Review


@role_required(User.Role.CUSTOMER)
def create(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related("food_listing__restaurant"),
        pk=reservation_id,
        customer=request.user,
    )
    if reservation.status != Reservation.Status.COLLECTED:
        messages.error(request, "You can review a meal after it has been collected.")
        return redirect("reservations:customer_list")
    if Review.objects.filter(reservation=reservation).exists():
        messages.info(request, "You have already reviewed this reservation.")
        return redirect("food:detail", pk=reservation.food_listing_id)

    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.customer = request.user
        review.restaurant = reservation.food_listing.restaurant
        review.food_listing = reservation.food_listing
        review.reservation = reservation
        review.full_clean()
        review.save()
        messages.success(request, "Thank you for sharing your review.")
        return redirect("food:detail", pk=reservation.food_listing_id)
    return render(request, "reviews/create.html", {"form": form, "reservation": reservation})
