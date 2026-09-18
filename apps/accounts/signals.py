"""Seed the initial admin (superuser) automatically after every ``migrate``.

Credentials come from environment variables (``ADMIN_EMAIL`` /
``ADMIN_PASSWORD``) and are never hardcoded. The operation is idempotent:
it creates the user when missing, otherwise it only enforces the
staff/superuser/active flags — an existing password is never reset.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


def seed_admin_user() -> str | None:
    """Create the seeded admin if needed. Returns a status message, or None
    when seeding is disabled or not configured."""
    if getattr(settings, "TESTING", False):
        return None
    email = (getattr(settings, "ADMIN_SEED_EMAIL", "") or "").strip()
    password = getattr(settings, "ADMIN_SEED_PASSWORD", "") or ""
    if not email or not password:
        return None
    user_model = get_user_model()
    email = user_model.objects.normalize_email(email)
    user, created = user_model.objects.get_or_create(email=email)
    if created:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        return f"Seeded admin user '{email}'."
    updates: dict[str, object] = {}
    for flag in ("is_staff", "is_superuser", "is_active"):
        if not getattr(user, flag):
            updates[flag] = True
    if updates:
        for key, value in updates.items():
            setattr(user, key, value)
        user.save(update_fields=list(updates))
        return f"Admin user '{email}' already exists; flags synced."
    return f"Admin user '{email}' already exists."


@receiver(post_migrate)
def seed_admin_after_migrate(sender, **kwargs):
    # post_migrate fires once per app; only act for this app so it runs once.
    if sender.name != "apps.accounts":
        return
    message = seed_admin_user()
    if message:
        print(message)
