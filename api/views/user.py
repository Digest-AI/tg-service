from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from api.models import User
from api.serializers import UserSerializer


@extend_schema_view(
    list=extend_schema(summary="List users", tags=["users"]),
    create=extend_schema(summary="Create user", tags=["users"]),
    retrieve=extend_schema(summary="Retrieve user by public_id", tags=["users"]),
    update=extend_schema(summary="Replace user by public_id", tags=["users"]),
    partial_update=extend_schema(summary="Partially update user by public_id", tags=["users"]),
    destroy=extend_schema(summary="Delete user by public_id", tags=["users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"
    lookup_value_regex = r"[^/]+"
