from rest_framework import serializers


class MatchDetailResponseSerializer(serializers.Serializer):
    match = serializers.DictField()


class TurnSubmitRequestSerializer(serializers.Serializer):
    action_code = serializers.CharField()
    info_target_key = serializers.CharField(required=False, allow_null=True)
    client_nonce = serializers.CharField()


class TurnSubmitResponseSerializer(serializers.Serializer):
    turn_result = serializers.DictField()
    match = serializers.DictField()


class MatchResultResponseSerializer(serializers.Serializer):
    result = serializers.DictField()
