from django.urls import path

from .views import dashboard


app_name = "admin_dashboard"

urlpatterns = [
    path("", dashboard, name="home"),
]
