from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import User, VerificationCode
from api.serializers import UserSerializer, VerifyCodeSerializer
from utils.exceptions.classes import BadRequest, NotFound


class VerifyCodeView(APIView):
    def post(self, request: Request) -> Response:
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code_value: str = serializer.validated_data["code"].upper()
        public_id: str = serializer.validated_data["public_id"]

        try:
            code = VerificationCode.objects.get(code=code_value)
        except VerificationCode.DoesNotExist:
            raise NotFound(detail="invalid_code", attr="code")

        if code.is_expired:
            code.delete()
            raise BadRequest(detail="code_expired", attr="code")

        username = code.username
        telegram_id = code.telegram_id
        code.delete()

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"public_id": public_id, "telegram_id": telegram_id},
        )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
