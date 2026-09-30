from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import RegisterSerializer


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    """Return an authentication error when a refresh token's user was deleted."""

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except get_user_model().DoesNotExist as exc:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                code="no_active_account",
            ) from exc


class SafeTokenRefreshView(TokenRefreshView):
    serializer_class = SafeTokenRefreshSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED
        )
