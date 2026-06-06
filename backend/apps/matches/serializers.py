from rest_framework import serializers


class MatchDetailResponseSerializer(serializers.Serializer):
    match = serializers.DictField()


class TurnSubmitRequestSerializer(serializers.Serializer):
    action_code = serializers.CharField()
    info_target_key = serializers.CharField(required=False, allow_null=True)
    client_nonce = serializers.UUIDField()


class TurnSubmitResponseSerializer(serializers.Serializer):
    turn_result = serializers.DictField()
    match = serializers.DictField()


class TurnLlmTextRequestSerializer(serializers.Serializer):
    display_slot = serializers.CharField(required=False, allow_null=True)


class TurnLlmTextResponseSerializer(serializers.Serializer):
    llm_text = serializers.DictField()


class DuelDialogueRequestSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=300)
    client_nonce = serializers.UUIDField()


class DuelDialogueResponseSerializer(serializers.Serializer):
    dialogue = serializers.DictField()


class MatchResultResponseSerializer(serializers.Serializer):
    result = serializers.DictField()
