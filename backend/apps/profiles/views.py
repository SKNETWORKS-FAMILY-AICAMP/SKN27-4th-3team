from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.common.runtime import api_success_response
from backend.apps.profiles import services as profile_services
from backend.apps.profiles.serializers import ProfileMeResponseSerializer


class ProfileMeView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = ProfileMeResponseSerializer

    def get(self, request):
        profile_me = profile_services.get_profile_me(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        )
        return api_success_response(
            request,
            {
                "user": profile_me.user,
                "profile": profile_me.profile,
            },
        )
