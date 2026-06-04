from rest_framework import serializers


class StoryCaseListResponseSerializer(serializers.Serializer):
    cases = serializers.ListField(child=serializers.DictField())


class StoryCaseBriefingResponseSerializer(serializers.Serializer):
    case = serializers.DictField()


class StoryCaseMatchStartRequestSerializer(serializers.Serializer):
    client_request_id = serializers.CharField()


class StoryCaseMatchStartResponseSerializer(serializers.Serializer):
    match = serializers.DictField()
