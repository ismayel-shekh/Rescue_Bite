from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("food.urls", "food"), namespace="food")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("reservations/", include(("reservations.urls", "reservations"), namespace="reservations")),
    path("restaurants/", include(("restaurants.urls", "restaurants"), namespace="restaurants")),
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),
    path("impact/", include(("impact.urls", "impact"), namespace="impact")),
    path("admin-dashboard/", include(("admin_dashboard.urls", "admin_dashboard"), namespace="admin_dashboard")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
