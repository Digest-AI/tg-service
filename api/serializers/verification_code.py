from rest_framework import serializers


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    public_id = serializers.CharField()
