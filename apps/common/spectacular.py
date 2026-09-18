"""drf-spectacular hooks so the docs match the real API.

The API wraps every 2xx JSON payload in ``{success, message, data}`` (see
``SuccessEnvelopeMixin``) and every error in ``{success, message, errors}``
(see ``custom_exception_handler``) — neither of which spectacular can infer.
This postprocessing hook rewrites the generated schema accordingly:

- 2xx ``application/json`` responses are wrapped in the success envelope
  (or the status envelope on ``_STATUS_ENVELOPE_PATHS``).
- Response examples are wrapped too, so they match the enveloped schema.
- Documented ``204``s become the real ``200 {"data": {}}`` DELETE contract.
- Shared ``ErrorEnvelope`` 400/401/403/404 responses are attached.
"""

from __future__ import annotations

MESSAGE_EXAMPLES = {
    "get": "Retrieved successfully.",
    "post": "Created successfully.",
    "put": "Updated successfully.",
    "patch": "Updated successfully.",
    "delete": "Deleted successfully.",
}

# Paths whose views set use_status_envelope = True (keep in sync with the views).
_VARIANT_VALUES_PATHS = {
    "/api/v1/productvarientvalues/{product_id}/",
    "/api/v1/productvarientvalues/{product_id}",
}

# Internal cron endpoints (apps.common.views.CronJobView): status envelope,
# shared-secret guard, and a 503 "disabled" contract.
_INTERNAL_CRON_PATHS = {
    "/api/v1/internal/cron/{job}/",
}

_VARIANT_IMAGES_PATHS = {
    "/api/v1/productvarientimages/{product_id}/",
    "/api/v1/productvarientimages/{product_id}",
    "/api/v1/productvarientimages/{product_id}/images/{image_id}/",
    "/api/v1/productvarientimages/{product_id}/images/{image_id}",
}

# Non-/admin paths that still require staff JWT (never marked public).
_STAFF_ONLY_PATHS = _VARIANT_VALUES_PATHS | _VARIANT_IMAGES_PATHS

_STATUS_ENVELOPE_PATHS = {
    "/api/v1/admin/products/",
    "/api/v1/admin/products/{id}/",
} | _STAFF_ONLY_PATHS | _INTERNAL_CRON_PATHS

_VARIANT_VALUES_MESSAGE = "ProductVarientValue created successfully"
_VARIANT_IMAGES_MESSAGES = {
    "get": "ProductVarientImages retrieved successfully",
    "post": "ProductVarientImage uploaded successfully",
    "delete": "ProductVarientImage deleted successfully",
}


def _status_message_example(path: str, method: str) -> str:
    """Mirror the views' success messages on status-envelope paths."""
    if path in _VARIANT_VALUES_PATHS:
        if method == "patch":
            return "ProductVarientValues updated successfully"
        return _VARIANT_VALUES_MESSAGE
    if path in _VARIANT_IMAGES_PATHS:
        return _VARIANT_IMAGES_MESSAGES.get(method, "Request successful.")
    if path in _INTERNAL_CRON_PATHS:
        return "Cron job 'tokens' completed."
    many = "{" not in path
    if method == "get":
        return "Products retrieved successfully." if many else "Product retrieved successfully."
    if method == "post":
        return "Product created successfully."
    if method in ("put", "patch"):
        return "Product updated successfully."
    if method == "delete":
        return "Product deleted successfully."
    return "Request successful."


def _status_envelope(payload_schema: dict, path: str, method: str, status_code) -> dict:
    return {
        "type": "object",
        "properties": {
            "status": {"type": "string", "example": "success"},
            "message": {"type": "string", "example": _status_message_example(path, method)},
            "statusCode": {"type": "integer", "example": int(status_code)},
            "data": payload_schema,
        },
        "required": ["status", "message", "statusCode", "data"],
    }


def _status_example(payload, path: str, method: str, status_code) -> dict:
    return {
        "status": "success",
        "message": _status_message_example(path, method),
        "statusCode": int(status_code),
        "data": payload,
    }


# POSTs whose views set a custom success_message (keep in sync with the views).
_MESSAGE_OVERRIDES = {
    "/api/v1/admin/auth/login/": "Login successful.",
    "/api/v1/admin/auth/refresh/": "Token refreshed successfully.",
    "/api/v1/admin/auth/logout/": "Successfully logged out.",
    "/api/v1/admin/auth/change-password/": "Password changed successfully.",
}

_ERROR_ENVELOPE = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": False},
        "message": {"type": "string", "example": "Validation failed."},
        "errors": {
            "type": "object",
            "description": "Field errors (or non_field_errors/detail).",
            "example": {"name": ["This field is required."]},
        },
    },
    "required": ["success", "message", "errors"],
}


def _message_example(path: str, method: str) -> str:
    if method == "post" and path in _MESSAGE_OVERRIDES:
        return _MESSAGE_OVERRIDES[path]
    return MESSAGE_EXAMPLES.get(method, "Request successful.")


def _success_envelope(payload_schema: dict, path: str, method: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "message": {"type": "string", "example": _message_example(path, method)},
            "data": payload_schema,
        },
        "required": ["success", "message", "data"],
    }


def _success_example(payload, path: str, method: str) -> dict:
    return {
        "success": True,
        "message": _message_example(path, method),
        "data": payload,
    }


def _error_response(description: str) -> dict:
    return {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorEnvelope"}
            }
        },
        "description": description,
    }


def envelope_postprocessing_hook(result, generator, request, public):
    """Wrap documented payloads in the real success/error envelopes."""
    components = result.setdefault("components", {}).setdefault("schemas", {})
    components.setdefault("ErrorEnvelope", _ERROR_ENVELOPE)

    for path, path_item in result.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        # Only /api/v1/admin/* requires auth; the rest of /api/v1/* is public.
        # Spectacular omits `security` for auth=[] views, which would inherit
        # the global lock — so public operations get an explicit empty list.
        is_public = (
            path.startswith("/api/v1/")
            and not path.startswith("/api/v1/admin/")
            and path not in _STAFF_ONLY_PATHS
        )
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(operation, dict):
                continue
            if is_public:
                operation["security"] = []
            responses = operation.setdefault("responses", {})

            use_status = path in _STATUS_ENVELOPE_PATHS
            if method == "delete" and "204" in responses and "200" not in responses:
                # Real DELETE contract: enveloped 200 with an empty object.
                empty = {"type": "object", "example": {}}
                schema = (
                    _status_envelope(empty, path, method, 200)
                    if use_status
                    else _success_envelope(empty, path, method)
                )
                responses["200"] = {
                    "content": {"application/json": {"schema": schema}},
                    "description": responses["204"].get("description")
                    or "Deleted successfully.",
                }
                del responses["204"]
            elif (
                method == "delete"
                and "200" in responses
                and "content" not in responses["200"]
            ):
                # APIView deletes document no body; the real contract is the
                # same enveloped 200 with an empty object.
                empty = {"type": "object", "example": {}}
                schema = (
                    _status_envelope(empty, path, method, 200)
                    if use_status
                    else _success_envelope(empty, path, method)
                )
                responses["200"] = {
                    "content": {"application/json": {"schema": schema}},
                    "description": responses["200"].get("description")
                    or "Deleted successfully.",
                }

            for status_code, response in responses.items():
                if not str(status_code).startswith("2"):
                    continue
                if not isinstance(response, dict):
                    continue
                media = response.get("content", {}).get("application/json")
                if not isinstance(media, dict) or "schema" not in media:
                    continue
                if use_status:
                    media["schema"] = _status_envelope(
                        media["schema"], path, method, status_code
                    )
                else:
                    media["schema"] = _success_envelope(media["schema"], path, method)
                # Response examples document the inner payload; wrap them so
                # they match the enveloped schema.
                if "example" in media:
                    if use_status:
                        media["example"] = _status_example(
                            media["example"], path, method, status_code
                        )
                    else:
                        media["example"] = _success_example(media["example"], path, method)
                for entry in (media.get("examples") or {}).values():
                    if isinstance(entry, dict) and "value" in entry:
                        if use_status:
                            entry["value"] = _status_example(
                                entry["value"], path, method, status_code
                            )
                        else:
                            entry["value"] = _success_example(entry["value"], path, method)

            # Documented error contract (never overwrites explicit responses).
            responses.setdefault("400", _error_response("Validation failed."))
            if operation.get("security", None) != []:
                responses.setdefault("401", _error_response("Authentication required."))
                responses.setdefault("403", _error_response("Permission denied."))
            if "{" in path and "}" in path:
                responses.setdefault("404", _error_response("Not found."))
            if path in _INTERNAL_CRON_PATHS:
                # Shared-secret guard: these are "public" (no bearer token) but
                # still reject a missing/wrong X-Cron-Secret header.
                responses.setdefault(
                    "403", _error_response("Missing or invalid X-Cron-Secret header.")
                )
                # Fail-closed contract: no usable CRON_SECRET -> 503, no work run.
                responses.setdefault(
                    "503",
                    _error_response(
                        "Cron endpoints disabled: CRON_SECRET is not configured."
                    ),
                )
    return result
