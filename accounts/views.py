from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import CustomerProfileForm, LoginForm, RegisterForm
from .models import User
from food.models import FoodListing
from impact.services import get_customer_impact


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role != role:
                if request.user.role == User.Role.RESTAURANT_OWNER:
                    return redirect("restaurants:dashboard")
                return redirect("accounts:customer_dashboard")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def register(request):
    if request.user.is_authenticated:
        return redirect("food:discover")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Rescue Bite!")
        if user.role == User.Role.RESTAURANT_OWNER:
            return redirect("restaurants:dashboard")
        return redirect("food:discover")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("food:discover")
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Welcome back!")
        if user.is_staff:
            return redirect("admin_dashboard:home")
        return redirect("food:discover")
    return render(request, "accounts/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("food:home")


@role_required(User.Role.CUSTOMER)
def customer_dashboard(request):
    active_listings = FoodListing.objects.filter(
        status=FoodListing.Status.ACTIVE,
        quantity__gt=0,
    ).select_related("restaurant")[:6]
    return render(
        request,
        "accounts/profile.html",
        {
            "profile": request.user.customer_profile,
            "active_listings": active_listings,
            "impact": get_customer_impact(request.user),
            "reservation_count": request.user.reservations.count(),
        },
    )


@role_required(User.Role.CUSTOMER)
def customer_reservations(request):
    from reservations.views import customer_list

    return customer_list(request)


@login_required
def profile(request):
    if request.user.role == User.Role.CUSTOMER:
        customer_profile = request.user.customer_profile
        form = CustomerProfileForm(request.POST or None, request.FILES or None, instance=customer_profile)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
        return render(
            request,
            "accounts/profile_edit.html",
            {
                "profile": customer_profile,
                "form": form,
                "impact": get_customer_impact(request.user),
            },
        )
    return redirect("restaurants:profile")
