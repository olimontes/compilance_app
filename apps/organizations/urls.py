from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MembershipViewSet, OrganizationUnitViewSet, OrganizationViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("organization-units", OrganizationUnitViewSet, basename="organization-unit")
router.register("memberships", MembershipViewSet, basename="membership")

urlpatterns = [
    path("", include(router.urls)),
]
