"""Admin authentication endpoints (JWT)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin

from .serializers import (
    AdminLoginResponseSerializer,
    AdminTokenObtainPairSerializer,
    AdminTokenRefreshResponseSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
)


@extend_schema(
    tags=["Admin - Auth"],
    responses={200: AdminLoginResponseSerializer},
    examples=[
        OpenApiExample(
            "Admin login",
            value={"email": "admin@example.com", "password": "change-me"},
            request_only=True,
        ),
        OpenApiExample(
            "Login tokens",
            value={
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "email": "admin@example.com",
                    "first_name": "",
                    "last_name": "",
                    "is_staff": True,
                    "is_active": True,
                    "date_joined": "2026-09-17T10:00:00Z",
                },
            },
            response_only=True,
        ),
    ],
)
class AdminLoginView(SuccessEnvelopeMixin, TokenObtainPairView):
    """Obtain a JWT access/refresh pair (staff users only)."""

    serializer_class = AdminTokenObtainPairSerializer
    success_message = "Login successful."


@extend_schema(tags=["Admin - Auth"], responses={200: AdminTokenRefreshResponseSerializer})
class AdminTokenRefreshView(SuccessEnvelopeMixin, TokenRefreshView):
    """Refresh an expired access token using a valid refresh token."""

    success_message = "Token refreshed successfully."


@extend_schema(tags=["Admin - Auth"], responses={200: OpenApiTypes.OBJECT})
class AdminLogoutView(SuccessEnvelopeMixin, GenericAPIView):
    """Blacklist a refresh token (JWT logout)."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    success_message = "Successfully logged out."

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response(
                {"refresh": ["Token is invalid or expired."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({}, status=status.HTTP_200_OK)


@extend_schema(tags=["Admin - Auth"], responses={200: OpenApiTypes.OBJECT})
class ChangePasswordView(SuccessEnvelopeMixin, GenericAPIView):
    """Change the current admin's password."""

    permission_classes = [IsAdminUser]
    serializer_class = ChangePasswordSerializer
    success_message = "Password changed successfully."

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({}, status=status.HTTP_200_OK)


@extend_schema(tags=["Admin - Auth"])
class AdminMeView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Return the current admin's profile."""

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    def get_object(self):
        return self.request.user
