from rest_framework.views import APIView

from backend.apps.profiles.serializers import ProfileMeResponseSerializer


class ProfileAPIServiceNotImplemented(NotImplementedError):
    pass


class ProfileMeView(APIView):
    response_serializer_class = ProfileMeResponseSerializer

    def get(self, request):
        raise ProfileAPIServiceNotImplemented("profile me service is not implemented")
