from rest_framework import serializers


class ProfileMeResponseSerializer(serializers.Serializer):
    user = serializers.DictField()
    profile = serializers.DictField()
