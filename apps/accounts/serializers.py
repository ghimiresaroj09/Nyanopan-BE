"""Admin-only authentication serializers (JWT via SimpleJWT)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """Safe admin representation. Never exposes password hashes."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "date_joined",
        ]
        read_only_fields = fields


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer: only staff users may obtain tokens."""

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            raise AuthenticationFailed("Admin access required.", code="admin_required")
        data["user"] = AdminUserSerializer(self.user).data
        return data


class AdminLoginResponseSerializer(serializers.Serializer):
    """JWT pair plus the admin profile returned by the login endpoint."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = AdminUserSerializer()


class AdminTokenRefreshResponseSerializer(serializers.Serializer):
    """Fresh access token returned by the refresh endpoint."""

    access = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    # write_only: the request takes the refresh token, the response is {}.
    refresh = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        new_password = attrs["new_password"]
        confirm = attrs.get("new_password_confirm")
        if confirm is not None and new_password != confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        if user.check_password(new_password):
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the old password."}
            )
        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages})
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
