from django.utils import timezone

from accounts.models import User

from .models import Notification


def notify_new_listing(listing):
    customers = User.objects.filter(role=User.Role.CUSTOMER, is_active=True)
    Notification.objects.bulk_create(
        [
            Notification(
                customer=customer,
                title="New food available",
                message=(
                    f"{listing.name} at {listing.restaurant.name} is now available at "
                    f"{listing.discount_percentage}% OFF."
                ),
                notification_type=Notification.Type.NEW_FOOD,
            )
            for customer in customers
        ]
    )


def notify_ending_soon(listing, customer):
    if listing.is_expired():
        return None
    return Notification.objects.create(
        customer=customer,
        title="Food ending soon",
        message=f"{listing.name} at {listing.restaurant.name} is ending soon.",
        notification_type=Notification.Type.ENDING_SOON,
    )
