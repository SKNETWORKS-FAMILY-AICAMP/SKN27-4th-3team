from rest_framework.views import APIView

from backend.apps.common.exceptions import ServiceNotImplementedError
from backend.apps.profiles.serializers import ProfileMeResponseSerializer


class ProfileAPIServiceNotImplemented(ServiceNotImplementedError):
    pass


class ProfileMeView(APIView):
    response_serializer_class = ProfileMeResponseSerializer

    def get(self, request):
        raise ProfileAPIServiceNotImplemented("profile.me")
