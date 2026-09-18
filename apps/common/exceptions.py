"""Consistent API error responses.

Every API error is returned as::

    {"success": false, "message": "...", "errors": {...}}

Successful responses keep standard DRF shapes (objects / paginated lists).
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

_STATUS_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Validation failed.",
    status.HTTP_401_UNAUTHORIZED: "Authentication required.",
    status.HTTP_403_FORBIDDEN: "Permission denied.",
    status.HTTP_404_NOT_FOUND: "Not found.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method not allowed.",
    status.HTTP_429_TOO_MANY_REQUESTS: "Too many requests.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal server error.",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Service unavailable.",
}


logger = logging.getLogger(__name__)


def _is_upload_rejection(exc) -> bool:
    """True for a 4xx-style rejection raised by the Cloudinary SDK.

    Imported lazily and matched by class so the handler still works when the
    Cloudinary packages are not installed.
    """
    try:
        from cloudinary.exceptions import BadRequest, Error, NotAllowed
    except ImportError:
        return False
    if isinstance(exc, (BadRequest, NotAllowed)):
        return True
    # Some SDK paths raise the generic Error for validation problems.
    return isinstance(exc, Error) and "unsupported" in str(exc).lower()


def to_drf_validation_error(exc: DjangoValidationError) -> DRFValidationError:
    """Convert a Django ValidationError to a DRF ValidationError (services layer)."""
    if hasattr(exc, "message_dict"):
        return DRFValidationError(exc.message_dict)
    return DRFValidationError({"non_field_errors": exc.messages})


def custom_exception_handler(exc, context):
    if _is_upload_rejection(exc):
        # Cloudinary refused the asset (bad/corrupt file, unsupported format,
        # account limit). That is the client's input, not a server fault.
        logger.warning("Image upload rejected by storage backend: %s", exc)
        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "errors": {"image": [str(exc) or "The uploaded file was rejected."]},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "success": False,
                "message": "Cannot delete this record because it is referenced by other records.",
                "errors": {
                    "non_field_errors": [
                        "This record is in use and cannot be deleted. "
                        "Deactivate it instead, or remove the referencing records first."
                    ]
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "success": False,
                "message": "Database integrity error.",
                "errors": {
                    "non_field_errors": [
                        "A record with these values already exists or a related record is missing."
                    ]
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "errors": getattr(exc, "message_dict", {"non_field_errors": exc.messages}),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, DjangoPermissionDenied):
        return Response(
            {
                "success": False,
                "message": "Permission denied.",
                "errors": {"detail": "Permission denied."},
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None
    message = _STATUS_MESSAGES.get(response.status_code, "Request failed.")
    response.data = {"success": False, "message": message, "errors": response.data}
    return response
