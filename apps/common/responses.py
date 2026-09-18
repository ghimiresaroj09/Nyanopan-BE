"""Success-response envelopes.

Default envelope for successful API responses::

    {"success": True, "message": "...", "data": <payload>}

Views that set ``use_status_envelope = True`` use the status envelope
instead::

    {"status": "success", "message": "...", "statusCode": 200, "data": <payload>}

``data`` holds the original payload untouched (an object, a paginated
``{count, next, previous, results}`` dict, or a list). Error responses keep
the ``{"success": False, ...}`` shape produced by the exception handler.
See ``apps.common.exceptions``.
"""

ACTION_MESSAGES = {
    "list": "Retrieved successfully.",
    "retrieve": "Retrieved successfully.",
    "create": "Created successfully.",
    "update": "Updated successfully.",
    "partial_update": "Updated successfully.",
    "destroy": "Deleted successfully.",
}

METHOD_MESSAGES = {
    "GET": "Request successful.",
    "POST": "Action successful.",
    "PUT": "Updated successfully.",
    "PATCH": "Updated successfully.",
    "DELETE": "Deleted successfully.",
}


class SuccessEnvelopeMixin:
    """Wrap 2xx responses in the success envelope.

    ``use_status_envelope = True`` switches a view to the status envelope
    (``{status, message, statusCode, data}``); the default stays legacy.
    """

    success_message: str | None = None
    use_status_envelope: bool = False

    def get_success_message(self, request) -> str:
        if self.success_message:
            return self.success_message
        action = getattr(self, "action", None)
        if action in ACTION_MESSAGES:
            return ACTION_MESSAGES[action]
        return METHOD_MESSAGES.get(request.method, "Request successful.")

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.method == "OPTIONS":
            return response
        if response.status_code < 200 or response.status_code >= 300:
            return response
        data = getattr(response, "data", None)
        if data is None:
            return response
        if isinstance(data, dict) and {"success", "message", "data"} <= set(data):
            return response  # already enveloped (legacy)
        if isinstance(data, dict) and {"status", "message", "statusCode", "data"} <= set(data):
            return response  # already enveloped (status)
        if getattr(self, "use_status_envelope", False):
            response.data = {
                "status": "success",
                "message": self.get_success_message(request),
                "statusCode": response.status_code,
                "data": data,
            }
            return response
        response.data = {
            "success": True,
            "message": self.get_success_message(request),
            "data": data,
        }
        return response
