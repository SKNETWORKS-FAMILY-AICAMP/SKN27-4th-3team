from rest_framework import serializers


class RagIngestRequestSerializer(serializers.Serializer):
    source_paths = serializers.ListField(
        child=serializers.CharField(allow_blank=False, trim_whitespace=True),
        min_length=1,
        max_length=20,
    )
    force = serializers.BooleanField(required=False, default=False)


class RagIngestResponseSerializer(serializers.Serializer):
    ingested_documents = serializers.IntegerField()
    ingested_chunks = serializers.IntegerField()
    skipped_documents = serializers.IntegerField()


class RagSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        min_length=1,
        max_length=300,
    )
    caller = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        min_length=1,
        max_length=80,
    )
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20)
    score_threshold = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)


class RagSearchResultSerializer(serializers.Serializer):
    document_id = serializers.CharField()
    chunk_id = serializers.CharField()
    source_path = serializers.CharField()
    score = serializers.FloatField()
    text_excerpt = serializers.CharField()


class RagSearchResponseSerializer(serializers.Serializer):
    results = RagSearchResultSerializer(many=True)
    top_k = serializers.IntegerField()
    score_threshold = serializers.FloatField()
