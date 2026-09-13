from django.db import models


class NotificationQuerySet(models.QuerySet):
    def for_customer(self, customer):
        return self.filter(customer=customer)

    def unread_for(self, customer):
        return self.for_customer(customer).filter(is_read=False)


class Notification(models.Model):
    class Type(models.TextChoices):
        RESERVATION = "RESERVATION", "Reservation"
        STATUS = "STATUS", "Status update"
        NEW_FOOD = "NEW_FOOD", "New food"
        ENDING_SOON = "ENDING_SOON", "Ending soon"

    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["customer", "is_read", "created_at"])]

    def __str__(self):
        return f"{self.title} for {self.customer.email}"
