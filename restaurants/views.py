from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import role_required
from food.forms import FoodListingForm
from food.models import FoodListing
from notifications.services import notify_new_listing

from .forms import RestaurantForm
from .models import Restaurant


def get_owner_restaurant(user):
    restaurant, _ = Restaurant.objects.get_or_create(
        owner=user,
        defaults={
            "name": f"{user.name}'s Restaurant",
            "address": "",
        },
    )
    return restaurant


@role_required(User.Role.RESTAURANT_OWNER)
def dashboard(request):
    restaurant = get_owner_restaurant(request.user)
    listings = restaurant.food_listings.select_related("restaurant")
    from reservations.models import Reservation

    owner_reservations = Reservation.objects.filter(food_listing__restaurant=restaurant)
    collected = owner_reservations.filter(status=Reservation.Status.COLLECTED)
    return render(
        request,
        "restaurants/dashboard.html",
        {
            "restaurant": restaurant,
            "listings": listings,
            "active_count": listings.filter(status=FoodListing.Status.ACTIVE, quantity__gt=0).count(),
            "total_count": listings.count(),
            "reservation_count": owner_reservations.count(),
            "meals_rescued": sum(item.quantity for item in collected),
            "revenue_recovered": sum(item.total_price for item in collected),
        },
    )


@role_required(User.Role.RESTAURANT_OWNER)
def profile(request):
    restaurant = get_owner_restaurant(request.user)
    form = RestaurantForm(request.POST or None, request.FILES or None, instance=restaurant)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Restaurant profile saved.")
        return redirect("restaurants:dashboard")
    return render(request, "restaurants/profile_form.html", {"form": form, "restaurant": restaurant})


@role_required(User.Role.RESTAURANT_OWNER)
def food_create(request):
    restaurant = get_owner_restaurant(request.user)
    form = FoodListingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        listing.restaurant = restaurant
        listing.full_clean()
        listing.save()
        notify_new_listing(listing)
        messages.success(request, f"{listing.name} is now available to rescue.")
        return redirect("restaurants:dashboard")
    return render(request, "restaurants/food_form.html", {"form": form, "restaurant": restaurant})


@role_required(User.Role.RESTAURANT_OWNER)
def food_edit(request, pk):
    restaurant = get_owner_restaurant(request.user)
    listing = get_object_or_404(FoodListing, pk=pk, restaurant=restaurant)
    form = FoodListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        listing.restaurant = restaurant
        listing.full_clean()
        listing.save()
        messages.success(request, "Food listing updated.")
        return redirect("restaurants:dashboard")
    return render(request, "restaurants/food_form.html", {"form": form, "listing": listing, "restaurant": restaurant})


# @role_required(User.Role.RESTAURANT_OWNER)
# def food_delete(request, pk):
#     restaurant = get_owner_restaurant(request.user)
#     listing = get_object_or_404(FoodListing, pk=pk, restaurant=restaurant)
#     if request.method == "POST":
#         listing.delete()
#         messages.success(request, "Food listing deleted.")
#     return redirect("restaurants:dashboard")

from reservations.models import Reservation


@role_required(User.Role.RESTAURANT_OWNER)
def food_delete(request, pk):
    restaurant = get_owner_restaurant(request.user)

    listing = get_object_or_404(
        FoodListing,
        pk=pk,
        restaurant=restaurant
    )

    if request.method == "POST":
        # Delete reservations connected to this food first
        Reservation.objects.filter(food_listing=listing).delete()

        # Now delete the food listing
        listing.delete()

        messages.success(request, "Food listing deleted successfully.")

    return redirect("restaurants:dashboard")

@role_required(User.Role.RESTAURANT_OWNER)
def reservation_list(request):
    from reservations.models import Reservation

    restaurant = get_owner_restaurant(request.user)
    reservations = Reservation.objects.filter(
        food_listing__restaurant=restaurant,
    ).select_related("customer", "food_listing")
    return render(
        request,
        "restaurants/reservation_list.html",
        {"restaurant": restaurant, "reservations": reservations},
    )
