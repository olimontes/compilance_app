from django.urls import path

from .views import error_probe, healthcheck

urlpatterns = [
    path("", healthcheck, name="healthcheck"),
    path("error-probe/", error_probe, name="error-probe"),
]
