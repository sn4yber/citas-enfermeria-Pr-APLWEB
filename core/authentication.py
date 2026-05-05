from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class EmailJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, validated_token = result
        return (user, validated_token)