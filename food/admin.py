from django.contrib import admin

from .models import FoodListing


@admin.register(FoodListing)
class FoodListingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "restaurant",
        "original_price",
        "discount_percentage",
        "discounted_price",
        "quantity",
        "status",
        "pickup_date",
        "pickup_end",
    )
    list_filter = ("status", "category", "pickup_date")
    search_fields = ("name", "restaurant__name", "pickup_location")
    readonly_fields = ("discounted_price", "created_at", "updated_at")
