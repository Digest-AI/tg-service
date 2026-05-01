from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.morning_digest import morning_digest_job


class MorningDigestTriggerRequestSerializer(serializers.Serializer):
    """Send an empty JSON object ``{}`` (no fields required)."""


class MorningDigestTriggerView(APIView):
    @extend_schema(
        summary="Run morning digest",
        description=(
            "Loads new recommendations from the recommendations service, "
            "refreshes event data from the parser for the relevant date range, "
            "and sends Telegram messages to linked users. "
            "Use from cron or another HTTP scheduler instead of an in-process cron."
        ),
        request=MorningDigestTriggerRequestSerializer,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(description="Digest run finished."),
        },
        tags=["digest"],
    )
    def post(self, request: Request) -> Response:
        morning_digest_job()
        return Response(status=status.HTTP_204_NO_CONTENT)
