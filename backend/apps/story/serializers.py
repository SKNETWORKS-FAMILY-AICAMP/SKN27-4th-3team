from rest_framework import serializers

from backend.apps.story.constants import PLAYER_DISPLAY_NAME_MAX_LENGTH


class StoryCaseListResponseSerializer(serializers.Serializer):
    cases = serializers.ListField(child=serializers.DictField())


class StoryCaseBriefingResponseSerializer(serializers.Serializer):
    case = serializers.DictField()


class StoryCaseMatchStartRequestSerializer(serializers.Serializer):
    client_request_id = serializers.UUIDField()
    player_display_name = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=False,
        max_length=PLAYER_DISPLAY_NAME_MAX_LENGTH,
        trim_whitespace=True,
    )


class StoryCaseMatchStartResponseSerializer(serializers.Serializer):
    match = serializers.DictField()
