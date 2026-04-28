from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import RecommendationView, UserViewSet, VerifyCodeView

router = SimpleRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("verification-codes/verify/", VerifyCodeView.as_view(), name="verify-code"),
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),
]
