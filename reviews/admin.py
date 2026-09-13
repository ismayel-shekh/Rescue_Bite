from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("food_listing", "restaurant", "customer", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("customer__email", "restaurant__name", "food_listing__name", "comment")
