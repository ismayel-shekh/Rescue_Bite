from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("reservation_code", "food_listing", "customer", "quantity", "total_price", "status", "created_at")
    list_filter = ("status", "created_at", "collected_at")
    search_fields = ("reservation_code", "customer__email", "customer__name", "food_listing__name")
    readonly_fields = ("reservation_code", "total_price", "created_at", "updated_at", "collected_at", "cancelled_at")
