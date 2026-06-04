from rest_framework import serializers


class SignupRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nickname = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class EmptyRequestSerializer(serializers.Serializer):
    pass


class CsrfResponseSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class SignupResponseSerializer(serializers.Serializer):
    user = serializers.DictField()


class LoginSessionSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    access_expires_in_seconds = serializers.IntegerField()


class LoginResponseSerializer(serializers.Serializer):
    user = serializers.DictField()
    profile = serializers.DictField()
    session = LoginSessionSerializer()


class LogoutResponseSerializer(serializers.Serializer):
    logged_out = serializers.BooleanField()


class RefreshResponseSerializer(serializers.Serializer):
    refreshed = serializers.BooleanField()
    access_expires_in_seconds = serializers.IntegerField()


class MeResponseSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    user = serializers.DictField()
    profile = serializers.DictField()
