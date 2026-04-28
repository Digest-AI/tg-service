from rest_framework import serializers


class RecommendationSerializer(serializers.Serializer):
    username = serializers.CharField()
    title = serializers.CharField()
    date = serializers.CharField()
    description = serializers.CharField()
    url = serializers.URLField()
