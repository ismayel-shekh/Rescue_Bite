from django.urls import path

from .views import customer_dashboard, customer_reservations, login_view, logout_view, profile, register


app_name = "accounts"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register, name="register"),
    path("logout/", logout_view, name="logout"),
    path("customer/dashboard/", customer_dashboard, name="customer_dashboard"),
    path("customer/reservations/", customer_reservations, name="customer_reservations"),
    path("profile/", profile, name="profile"),
]
