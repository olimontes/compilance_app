from rest_framework import generics

from .models import UserPreference, UserProfile
from .serializers import UserPreferenceSerializer, UserProfileSerializer


class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        profile, _created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.get_full_name() or self.request.user.get_username()},
        )
        return profile


class CurrentUserPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer

    def get_object(self):
        preferences, _created = UserPreference.objects.get_or_create(user=self.request.user)
        return preferences
