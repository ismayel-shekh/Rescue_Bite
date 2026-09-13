from django.urls import path

from .views import dashboard


app_name = "impact"
urlpatterns = [path("", dashboard, name="dashboard")]
