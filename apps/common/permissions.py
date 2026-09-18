from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to authenticated staff (administrator) users.

    There are no customer accounts in this project; every protected endpoint
    is admin-only.
    """

    message = "Admin access required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
