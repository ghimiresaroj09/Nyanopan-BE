from django.urls import path

from .views import (
    AdminLoginView,
    AdminLogoutView,
    AdminMeView,
    AdminTokenRefreshView,
    ChangePasswordView,
)

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("refresh/", AdminTokenRefreshView.as_view(), name="admin-token-refresh"),
    path("logout/", AdminLogoutView.as_view(), name="admin-logout"),
    path("change-password/", ChangePasswordView.as_view(), name="admin-change-password"),
    path("me/", AdminMeView.as_view(), name="admin-me"),
]
