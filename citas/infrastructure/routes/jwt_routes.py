from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework.throttling import AnonRateThrottle

class ThrottledTokenView(TokenObtainPairView):
    throttle_classes = [AnonRateThrottle]

urlpatterns = [
    path('token/', ThrottledTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]