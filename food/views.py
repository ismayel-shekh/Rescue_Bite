from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from impact.services import get_customer_impact

from .models import FoodListing


DEFAULT_FOOD_IMAGES = [
    "https://images.unsplash.com/photo-1512621776951-a57141f2e346?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=1200&q=85",
]

TESTIMONIALS = [
    {
        "quote": "Rescue Bite makes it easy to find a warm, affordable meal after class while knowing I am helping reduce waste.",
        "name": "Aiman Rahman",
        "role": "AIU student",
        "initial": "A",
    },
    {
        "quote": "We recover value from food that might otherwise be thrown away, and new customers discover our kitchen.",
        "name": "Nadia Karim",
        "role": "Restaurant owner",
        "initial": "N",
    },
    {
        "quote": "The pickup process is simple, the prices are fair, and every collected meal feels like a small win for the community.",
        "name": "Daniel Lim",
        "role": "Rescue Bite customer",
        "initial": "D",
    },
]


def refresh_active_statuses():
    for listing in FoodListing.objects.filter(status=FoodListing.Status.ACTIVE):
        listing.refresh_status()


def home(request):
    refresh_active_statuses()
    featured_listings = list(FoodListing.objects.filter(
        status=FoodListing.Status.ACTIVE,
        quantity__gt=0,
    ).select_related("restaurant")[:6])
    collage_images = [listing.display_image for listing in featured_listings if listing.display_image]
    collage_images.extend(DEFAULT_FOOD_IMAGES)
    menu_groups = [
        {"label": "Breakfast", "caption": "Fresh starts, rescued early.", "listings": featured_listings[:2]},
        {"label": "Lunch", "caption": "Good food for less, midday.", "listings": featured_listings[2:4]},
        {"label": "Dinner", "caption": "Collect before closing time.", "listings": featured_listings[4:6]},
    ]
    return render(
        request,
        "food/home.html",
        {
            "featured_listings": featured_listings,
            "hero_image": featured_listings[0].display_image if featured_listings else DEFAULT_FOOD_IMAGES[0],
            "collage_images": collage_images[:4],
            "menu_groups": menu_groups,
            "testimonials": TESTIMONIALS,
        },
    )


def discover(request):
    refresh_active_statuses()
    listings = FoodListing.objects.filter(
        status=FoodListing.Status.ACTIVE,
        quantity__gt=0,
    ).select_related("restaurant")

    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    location = request.GET.get("location", "").strip()
    min_discount = request.GET.get("min_discount", "")
    max_price = request.GET.get("max_price", "")
    sort = request.GET.get("sort", "newest")

    if query:
        listings = listings.filter(Q(name__icontains=query) | Q(restaurant__name__icontains=query))
    if category:
        listings = listings.filter(category=category)
    if location:
        listings = listings.filter(
            Q(pickup_location__icontains=location)
            | Q(restaurant__location__icontains=location)
            | Q(restaurant__address__icontains=location)
        )
    if min_discount.isdigit():
        listings = listings.filter(discount_percentage__gte=int(min_discount))
    if max_price:
        try:
            listings = listings.filter(discounted_price__lte=max_price)
        except (TypeError, ValueError):
            pass

    sort_map = {
        "highest_discount": "-discount_percentage",
        "lowest_price": "discounted_price",
        "ending_soon": "pickup_end",
        "newest": "-created_at",
    }
    listings = listings.order_by(sort_map.get(sort, "-created_at"))
    context = {
        "listings": listings,
        "categories": FoodListing.Category.choices,
        "filters": request.GET,
    }
    if request.user.is_authenticated and request.user.role == User.Role.CUSTOMER:
        context["impact"] = get_customer_impact(request.user)
    return render(request, "food/discover.html", context)


def detail(request, pk):
    listing = get_object_or_404(FoodListing.objects.select_related("restaurant"), pk=pk)
    listing.refresh_status()
    reviews = listing.reviews.select_related("customer")
    rating_values = [review.rating for review in reviews]
    average_rating = round(sum(rating_values) / len(rating_values), 1) if rating_values else None
    return render(
        request,
        "food/detail.html",
        {"listing": listing, "reviews": reviews, "average_rating": average_rating},
    )
