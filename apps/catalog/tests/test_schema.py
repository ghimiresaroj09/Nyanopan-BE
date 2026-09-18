"""OpenAPI schema contract: envelope, DELETE-200, public auth, error envelope."""

import pytest
from drf_spectacular.generators import SchemaGenerator


@pytest.fixture(scope="module")
def api_schema():
    return SchemaGenerator().get_schema(request=None, public=True)


def _response(api_schema, path, method, status):
    return api_schema["paths"][path][method]["responses"][str(status)]


class TestSuccessEnvelope:
    def test_upload_response_is_enveloped(self, api_schema):
        media = _response(api_schema, "/api/v1/admin/images/upload/", "post", 201)[
            "content"
        ]["application/json"]
        props = media["schema"]["properties"]
        assert set(props) == {"success", "message", "data"}
        assert props["data"]["$ref"].endswith("/ImageUploadResponse")

    def test_list_response_is_enveloped(self, api_schema):
        media = _response(api_schema, "/api/v1/admin/categories/", "get", 200)[
            "content"
        ]["application/json"]
        assert set(media["schema"]["properties"]) == {"success", "message", "data"}

    def test_product_response_uses_status_envelope(self, api_schema):
        media = _response(api_schema, "/api/v1/admin/products/", "post", 201)[
            "content"
        ]["application/json"]
        props = media["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert props["data"]["$ref"].endswith("/ProductAdminResponse")

    def test_variant_values_response_uses_status_envelope(self, api_schema):
        media = _response(
            api_schema, "/api/v1/productvarientvalues/{product_id}/", "post", 201
        )["content"]["application/json"]
        props = media["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert (
            props["message"]["example"] == "ProductVarientValue created successfully"
        )
        assert props["data"]["$ref"].endswith("/ProductVariantValuesResponse")

    def test_variant_values_documents_staff_auth(self, api_schema):
        operation = api_schema["paths"]["/api/v1/productvarientvalues/{product_id}/"][
            "post"
        ]
        assert operation.get("security", None) != []
        assert "401" in operation["responses"]
        assert "403" in operation["responses"]

    def test_variant_images_responses_use_status_envelope(self, api_schema):
        listing = _response(
            api_schema, "/api/v1/productvarientimages/{product_id}/", "get", 200
        )["content"]["application/json"]
        props = listing["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert (
            props["message"]["example"]
            == "ProductVarientImages retrieved successfully"
        )
        assert props["data"]["$ref"].endswith("/ProductVariantImagesResponse")

        upload = _response(
            api_schema, "/api/v1/productvarientimages/{product_id}/", "post", 201
        )["content"]["application/json"]
        props = upload["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert (
            props["message"]["example"] == "ProductVarientImage uploaded successfully"
        )
        assert props["data"]["$ref"].endswith("/ProductVariantImageUploadResponse")

        delete = _response(
            api_schema,
            "/api/v1/productvarientimages/{product_id}/images/{image_id}/",
            "delete",
            200,
        )["content"]["application/json"]
        props = delete["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert (
            props["message"]["example"] == "ProductVarientImage deleted successfully"
        )

    def test_variant_images_upload_documents_json_and_multipart(self, api_schema):
        content = _request_body(
            api_schema, "/api/v1/productvarientimages/{product_id}/", "post"
        )
        assert set(content) == {"application/json", "multipart/form-data"}
        assert content["application/json"]["schema"]["$ref"].endswith(
            "/ProductVariantImagesUploadRequest"
        )
        assert content["multipart/form-data"]["schema"]["$ref"].endswith(
            "/ProductVariantImagesMultipartRequest"
        )

    def test_variant_images_documents_staff_auth(self, api_schema):
        for path, method in [
            ("/api/v1/productvarientimages/{product_id}/", "get"),
            (
                "/api/v1/productvarientimages/{product_id}/images/{image_id}/",
                "delete",
            ),
        ]:
            operation = api_schema["paths"][path][method]
            assert operation.get("security", None) != []
            assert "401" in operation["responses"]
            assert "403" in operation["responses"]

    def test_delete_documents_200_not_204(self, api_schema):
        responses = api_schema["paths"]["/api/v1/admin/categories/{id}/"]["delete"][
            "responses"
        ]
        assert "204" not in responses
        props = responses["200"]["content"]["application/json"]["schema"]["properties"]
        assert set(props) == {"success", "message", "data"}


class TestErrorEnvelope:
    def test_error_component_exists(self, api_schema):
        props = api_schema["components"]["schemas"]["ErrorEnvelope"]["properties"]
        assert set(props) == {"success", "message", "errors"}

    def test_unsafe_operation_has_400_401_403(self, api_schema):
        responses = api_schema["paths"]["/api/v1/admin/images/upload/"]["post"][
            "responses"
        ]
        for code in ("400", "401", "403"):
            ref = responses[code]["content"]["application/json"]["schema"]["$ref"]
            assert ref == "#/components/schemas/ErrorEnvelope"

    def test_detail_operation_has_404(self, api_schema):
        responses = api_schema["paths"]["/api/v1/admin/categories/{id}/"]["get"][
            "responses"
        ]
        ref = responses["404"]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorEnvelope"


class TestSecurity:
    def test_public_endpoints_have_no_security(self, api_schema):
        operation = api_schema["paths"]["/api/v1/categories/"]["get"]
        assert operation.get("security") == []
        assert "401" not in operation["responses"]

    def test_admin_endpoints_require_auth(self, api_schema):
        operation = api_schema["paths"]["/api/v1/admin/images/upload/"]["post"]
        assert operation.get("security") not in (None, [])

    def test_only_jwt_auth_scheme_is_offered(self, api_schema):
        schemes = api_schema["components"]["securitySchemes"]
        assert set(schemes) == {"jwtAuth"}
        assert schemes["jwtAuth"] == {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        operation = api_schema["paths"]["/api/v1/admin/images/upload/"]["post"]
        assert operation["security"] == [{"jwtAuth": []}]
def _request_body(api_schema, path, method):
    return api_schema["paths"][path][method]["requestBody"]["content"]


def _enveloped_data(api_schema, path, method, status):
    return _response(api_schema, path, method, status)["content"]["application/json"][
        "schema"
    ]["properties"]["data"]


class TestRequestBodies:
    @pytest.mark.parametrize(
        "path,json_ref,multipart_ref",
        [
            (
                "/api/v1/admin/categories/",
                "CategoryAdminRequest",
                "CategoryMultipartRequest",
            ),
            (
                "/api/v1/admin/product-attribute-values/",
                "ProductAttributeValueAdminRequest",
                "ProductAttributeValueMultipartRequest",
            ),
            (
                "/api/v1/admin/products/",
                "ProductAdminWriteRequest",
                "ProductMultipartRequest",
            ),
        ],
    )
    def test_image_endpoints_document_json_and_multipart_bodies(
        self, api_schema, path, json_ref, multipart_ref
    ):
        content = _request_body(api_schema, path, "post")
        assert set(content) == {"application/json", "multipart/form-data"}
        assert content["application/json"]["schema"]["$ref"].endswith(f"/{json_ref}")
        assert content["multipart/form-data"]["schema"]["$ref"].endswith(
            f"/{multipart_ref}"
        )

    def test_category_json_body_has_request_example(self, api_schema):
        examples = _request_body(api_schema, "/api/v1/admin/categories/", "post")[
            "application/json"
        ]["examples"]
        assert "CategoryWithImageReference" in examples

    def test_image_object_request_has_write_only_markers(self, api_schema):
        props = api_schema["components"]["schemas"]["CategoryAdminRequest"][
            "properties"
        ]["image"]["properties"]
        assert props["name"]["writeOnly"] is True
        assert props["file"]["writeOnly"] is True
        assert "writeOnly" not in props["url"]
        assert "writeOnly" not in props["public_id"]

    def test_public_category_image_omits_public_id(self, api_schema):
        props = api_schema["components"]["schemas"]["CategoryPublic"]["properties"][
            "image"
        ]["properties"]
        assert set(props) == {"url", "title", "caption", "alt"}

    def test_option_reference_accepts_uuid_key_or_object(self, api_schema):
        items = api_schema["components"]["schemas"]["VariantNestedRequest"][
            "properties"
        ]["options"]["items"]
        assert len(items["oneOf"]) == 3


class TestResponseBodies:
    def test_product_create_returns_response_shape(self, api_schema):
        data = _enveloped_data(api_schema, "/api/v1/admin/products/", "post", 201)
        assert data["$ref"].endswith("/ProductAdminResponse")

    @pytest.mark.parametrize("method", ["put", "patch"])
    def test_product_update_returns_response_shape(self, api_schema, method):
        data = _enveloped_data(
            api_schema, "/api/v1/admin/products/{id}/", method, 200
        )
        assert data["$ref"].endswith("/ProductAdminResponse")

    def test_image_delete_returns_deleted_flag(self, api_schema):
        data = _enveloped_data(api_schema, "/api/v1/admin/images/delete/", "post", 200)
        assert data["$ref"].endswith("/ImageDeleteResponse")
        props = api_schema["components"]["schemas"]["ImageDeleteResponse"]["properties"]
        assert props["deleted"] == {"type": "boolean"}

    def test_login_returns_tokens_and_user(self, api_schema):
        data = _enveloped_data(api_schema, "/api/v1/admin/auth/login/", "post", 200)
        assert data["$ref"].endswith("/AdminLoginResponse")
        props = api_schema["components"]["schemas"]["AdminLoginResponse"]["properties"]
        assert set(props) == {"access", "refresh", "user"}

    def test_refresh_returns_access_only(self, api_schema):
        data = _enveloped_data(api_schema, "/api/v1/admin/auth/refresh/", "post", 200)
        assert data["$ref"].endswith("/AdminTokenRefreshResponse")
        props = api_schema["components"]["schemas"]["AdminTokenRefreshResponse"][
            "properties"
        ]
        assert set(props) == {"access"}

    def test_logout_returns_empty_object(self, api_schema):
        data = _enveloped_data(api_schema, "/api/v1/admin/auth/logout/", "post", 200)
        assert "$ref" not in data
        assert "refresh" not in data.get("properties", {})

    def test_public_detail_ids_are_uuids(self, api_schema):
        props = api_schema["components"]["schemas"]["ProductDetail"]["properties"]
        attribute = props["attributes"]["items"]["properties"]
        assert attribute["id"] == {"type": "string", "format": "uuid"}
        value = attribute["values"]["items"]["properties"]
        assert value["id"] == {"type": "string", "format": "uuid"}
        assert "url" in value["additional_images"]["items"]["properties"]
        variant = props["variants"]["items"]["properties"]
        assert variant["id"] == {"type": "string", "format": "uuid"}
        option = variant["options"]["items"]["properties"]
        assert option["product_attribute_value"] == {"type": "string", "format": "uuid"}

    def test_login_response_example_is_enveloped(self, api_schema):
        media = _response(api_schema, "/api/v1/admin/auth/login/", "post", 200)[
            "content"
        ]["application/json"]
        value = media["examples"]["LoginTokens"]["value"]
        assert set(value) == {"success", "message", "data"}
        assert set(value["data"]) == {"access", "refresh", "user"}


class TestProductFlowPresentation:
    """Swagger presents product creation as 3 ordered step tags."""

    FLOW_TAGS = [
        "Product 1/3 - Info",
        "Product 2/3 - Attributes, Values & Price",
        "Product 3/3 - Images",
    ]

    def test_flow_tags_are_ordered_ahead_of_admin_tags(self, api_schema):
        names = [tag["name"] for tag in api_schema["tags"]]
        positions = [names.index(name) for name in self.FLOW_TAGS]
        assert positions == sorted(positions)
        assert max(positions) < names.index("Admin - Categories")
        for tag in api_schema["tags"]:
            if tag["name"] in self.FLOW_TAGS:
                assert tag["description"].startswith("Step ")

    def test_step1_product_info_presentation(self, api_schema):
        create = api_schema["paths"]["/api/v1/admin/products/"]["post"]
        assert create["tags"] == ["Product 1/3 - Info"]
        assert create["summary"] == "Step 1: Add product info"
        assert "Step 1 of the product flow" in create["description"]

    def test_step2_variant_values_presentation(self, api_schema):
        post = api_schema["paths"]["/api/v1/productvarientvalues/{product_id}/"][
            "post"
        ]
        assert post["tags"] == ["Product 2/3 - Attributes, Values & Price"]
        assert post["summary"] == "Step 2: Add attributes, values & prices"
        assert "Step 2 of the product flow" in post["description"]

    def test_step3_variant_images_presentation(self, api_schema):
        collection = api_schema["paths"][
            "/api/v1/productvarientimages/{product_id}/"
        ]
        assert collection["get"]["tags"] == ["Product 3/3 - Images"]
        assert collection["post"]["tags"] == ["Product 3/3 - Images"]
        assert collection["post"]["summary"] == "Step 3: Upload images"
        assert "Step 3 of the product flow" in collection["post"]["description"]
        delete = api_schema["paths"][
            "/api/v1/productvarientimages/{product_id}/images/{image_id}/"
        ]["delete"]
        assert delete["tags"] == ["Product 3/3 - Images"]
        assert delete["summary"] == "Delete a gallery image"


class TestVariantValuesPatch:
    PATH = "/api/v1/productvarientvalues/{product_id}/"

    def test_patch_operation_presentation(self, api_schema):
        operation = api_schema["paths"][self.PATH]["patch"]
        assert operation["tags"] == ["Product 2/3 - Attributes, Values & Price"]
        assert operation["summary"] == "Step 2: Bulk update prices & flags"
        assert "bulk-update" in operation["description"]
        assert operation.get("security", None) != []
        assert set(operation["responses"]) >= {
            "200",
            "400",
            "401",
            "403",
            "404",
        }

    def test_patch_request_body(self, api_schema):
        content = api_schema["paths"][self.PATH]["patch"]["requestBody"]["content"]
        ref = content["application/json"]["schema"]["$ref"]
        assert ref.endswith("/PatchedProductVariantValuesPatchRequest")
        schemas = api_schema["components"]["schemas"]
        top = schemas["PatchedProductVariantValuesPatchRequest"]
        assert "required" not in top  # PATCH convention: all fields optional
        row_ref = top["properties"]["generatedVarients"]["items"]["$ref"]
        assert row_ref.endswith("/GeneratedVariantPatchRequest")
        row = schemas["GeneratedVariantPatchRequest"]
        assert row["required"] == ["sku"]
        assert set(row["properties"]) == {
            "sku",
            "name",
            "price",
            "is_active",
            "is_special_edition",
        }

    def test_patch_response_is_enveloped(self, api_schema):
        media = _response(api_schema, self.PATH, "patch", 200)["content"][
            "application/json"
        ]
        props = media["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert (
            props["message"]["example"] == "ProductVarientValues updated successfully"
        )
        assert props["data"]["$ref"].endswith("/ProductVariantValuesResponse")


class TestInternalCronPresentation:
    """The scheduler entry points must be documented, public, and guarded."""

    PATH = "/api/v1/internal/cron/{job}/"

    def test_get_and_post_are_documented_under_internal(self, api_schema):
        path_item = api_schema["paths"][self.PATH]
        assert set(path_item) >= {"get", "post"}
        for method in ("get", "post"):
            operation = path_item[method]
            assert operation["tags"] == ["Internal"]
            assert operation["summary"] == "Run a scheduled maintenance job"
            assert "X-Cron-Secret" in operation["description"]

    def test_job_parameter_is_documented(self, api_schema):
        params = api_schema["paths"][self.PATH]["get"]["parameters"]
        assert [p["name"] for p in params] == ["job"]
        assert params[0]["in"] == "path"
        assert params[0]["required"] is True

    def test_no_bearer_token_required(self, api_schema):
        """The secret travels in a header, so the endpoints are not JWT-locked."""
        for method in ("get", "post"):
            assert api_schema["paths"][self.PATH][method]["security"] == []

    def test_documents_the_guard_and_disable_contract(self, api_schema):
        for status in ("403", "503"):
            media = api_schema["paths"][self.PATH]["get"]["responses"][status]["content"][
                "application/json"
            ]
            assert media["schema"]["$ref"].endswith("/ErrorEnvelope")

    def test_response_uses_status_envelope(self, api_schema):
        media = _response(api_schema, self.PATH, "get", 200)["content"]["application/json"]
        props = media["schema"]["properties"]
        assert set(props) == {"status", "message", "statusCode", "data"}
        assert props["message"]["example"] == "Cron job 'tokens' completed."
        assert props["statusCode"]["example"] == 200
