from django.urls import path

from .views import CurrentUserPreferenceView, CurrentUserProfileView

urlpatterns = [
    path("user-profile/me/", CurrentUserProfileView.as_view(), name="current-user-profile"),
    path("user-preferences/me/", CurrentUserPreferenceView.as_view(), name="current-user-preferences"),
]
