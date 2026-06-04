from django.db import models
from pgvector.django import VectorField


class RetrievalDocument(models.Model):
    document_id = models.TextField()
    source_path = models.TextField()
    schema_version = models.TextField()


class RetrievalChunk(models.Model):
    document_id = models.TextField()
    chunk_id = models.TextField()
    source_path = models.TextField()
    schema_version = models.TextField()
    content = models.TextField()
    embedding = VectorField()


class RetrievalQueryLog(models.Model):
    query = models.TextField()
    caller = models.TextField()
    document_id = models.TextField()
    chunk_id = models.TextField()
    score = models.FloatField()
    threshold = models.FloatField()
    top_k = models.PositiveIntegerField()
    created_at = models.DateTimeField()
