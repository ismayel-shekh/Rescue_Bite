from django.urls import path

from .views import cancel, collect, confirmation, create, customer_list


app_name = "reservations"
urlpatterns = [
    path("food/<int:listing_id>/reserve/", create, name="create"),
    path("confirmation/<str:code>/", confirmation, name="confirmation"),
    path("my/", customer_list, name="customer_list"),
    path("<int:pk>/cancel/", cancel, name="cancel"),
    path("<int:pk>/collect/", collect, name="collect"),
]
