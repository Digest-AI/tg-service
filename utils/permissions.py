from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    def has_permission(self, request, view) -> bool:
        secret = request.headers.get("X-Service-Secret")
        return bool(secret and secret == settings.SERVICE_SECRET)
