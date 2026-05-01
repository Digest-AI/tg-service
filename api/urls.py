from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import MorningDigestTriggerView, TelegramWebhookView, UserViewSet, VerifyCodeView

router = SimpleRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("verification-codes/verify/", VerifyCodeView.as_view(), name="verify-code"),
    path("digest/morning/", MorningDigestTriggerView.as_view(), name="morning-digest"),
    path("webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
]
