"""Image uploads: storage backends, validation, and delete.

Uploads run against the real filesystem fallback (``USE_CLOUDINARY=False`` in
the test settings), so no credentials or network access are needed. What the
tests verify is the wiring that is identical in both modes: the ``image``
multipart contract, validation, permissions, and the API envelope.
"""

import io
import json

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from conftest import status_data, success_data

pytestmark = pytest.mark.django_db

UPLOAD_URL = "/api/v1/admin/images/upload/"
DELETE_URL = "/api/v1/admin/images/delete/"


def _bytes_image(format="PNG", color="green") -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color).save(buffer, format=format)
    return buffer.getvalue()


def _image_file(name="photo.png"):
    return SimpleUploadedFile(name, _bytes_image(), content_type="image/png")


def _post_upload(client, payload, tmp_path):
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        return client.post(UPLOAD_URL, payload, format="multipart")


class TestImageUpload:
    def test_upload_returns_url_and_public_id(self, admin_client, tmp_path):
        data = success_data(
            _post_upload(admin_client, {"image": _image_file()}, tmp_path),
            status_code=201,
        )
        assert data["url"].startswith("http://testserver/media/test/")
        assert data["public_id"].startswith("test/")
        assert data["public_id"].endswith(".png")
        assert (data["width"], data["height"], data["format"]) == (1, 1, "png")
        assert (tmp_path / data["public_id"]).is_file()

    def test_upload_custom_folder(self, admin_client, tmp_path):
        data = success_data(
            _post_upload(
                admin_client, {"image": _image_file(), "folder": "products"}, tmp_path
            ),
            status_code=201,
        )
        assert data["public_id"].startswith("products/")

    def test_upload_requires_image_field(self, admin_client, tmp_path):
        response = _post_upload(admin_client, {}, tmp_path)
        assert response.status_code == 400
        assert "image" in response.data["errors"]

    def test_legacy_file_field_rejected(self, admin_client, tmp_path):
        response = _post_upload(admin_client, {"file": _image_file()}, tmp_path)
        assert response.status_code == 400
        assert "image" in response.data["errors"]

    def test_rejects_non_image_content(self, admin_client, tmp_path):
        bad = SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png")
        response = _post_upload(admin_client, {"image": bad}, tmp_path)
        assert response.status_code == 400
        assert "image" in response.data["errors"]

    def test_rejects_disallowed_extension(self, admin_client, tmp_path):
        bmp = SimpleUploadedFile(
            "photo.bmp", _bytes_image(format="BMP"), content_type="image/bmp"
        )
        response = _post_upload(admin_client, {"image": bmp}, tmp_path)
        assert response.status_code == 400
        assert "Unsupported image format" in str(response.data["errors"]["image"])

    def test_rejects_oversized_image(self, admin_client, tmp_path):
        with override_settings(MEDIA_ROOT=str(tmp_path), MAX_IMAGE_UPLOAD_MB=0):
            response = admin_client.post(
                UPLOAD_URL, {"image": _image_file()}, format="multipart"
            )
        assert response.status_code == 400
        assert "image" in response.data["errors"]

    def test_upload_denied_for_anonymous(self, api_client, tmp_path):
        response = _post_upload(api_client, {"image": _image_file()}, tmp_path)
        assert response.status_code == 401

    def test_upload_denied_for_non_admin(self, plain_client, tmp_path):
        response = _post_upload(plain_client, {"image": _image_file()}, tmp_path)
        assert response.status_code == 403


class TestImageDelete:
    def test_delete_uploaded_file(self, admin_client, tmp_path):
        data = success_data(
            _post_upload(admin_client, {"image": _image_file()}, tmp_path),
            status_code=201,
        )
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            deleted = success_data(
                admin_client.post(
                    DELETE_URL, {"public_id": data["public_id"]}, format="json"
                )
            )
        assert deleted == {"deleted": True}
        assert not (tmp_path / data["public_id"]).is_file()

    def test_delete_missing_returns_false(self, admin_client, tmp_path):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = success_data(
                admin_client.post(
                    DELETE_URL, {"public_id": "test/missing.png"}, format="json"
                )
            )
        assert data == {"deleted": False}

    def test_delete_rejects_traversal(self, admin_client, tmp_path):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = success_data(
                admin_client.post(
                    DELETE_URL, {"public_id": "../../etc/passwd"}, format="json"
                )
            )
        assert data == {"deleted": False}


class TestStorageSelection:
    def test_falls_back_to_filesystem(self, settings):
        from apps.common.storages import image_storage

        assert settings.USE_CLOUDINARY is False
        assert isinstance(image_storage(), FileSystemStorage)

    def test_uses_cloudinary_when_enabled(self, settings):
        pytest.importorskip("cloudinary_storage")
        from cloudinary_storage.storage import MediaCloudinaryStorage

        from apps.common.storages import image_storage

        settings.USE_CLOUDINARY = True
        storage = image_storage()
        assert isinstance(storage, MediaCloudinaryStorage)
        assert storage.RESOURCE_TYPE == "image"

    def test_cloudinary_rejection_maps_to_400(self):
        from cloudinary.exceptions import BadRequest

        from apps.common.exceptions import custom_exception_handler

        response = custom_exception_handler(
            BadRequest("Unsupported video format or file"), None
        )
        assert response.status_code == 400
        assert response.data["success"] is False
        assert "image" in response.data["errors"]


TEST_HOST = "example.com"  # dotted host: Django URLValidator rejects "testserver"


def _post_multipart(client, url, payload, tmp_path):
    with override_settings(
        MEDIA_ROOT=str(tmp_path), ALLOWED_HOSTS=["testserver", TEST_HOST]
    ):
        return client.post(url, payload, format="multipart", HTTP_HOST=TEST_HOST)


class TestCategoryImageUpload:
    URL = "/api/v1/admin/categories/"

    def test_category_multipart_image(self, admin_client, tmp_path):
        data = success_data(
            _post_multipart(
                admin_client,
                self.URL,
                {"name": "Multipart Hats", "image": _image_file()},
                tmp_path,
            ),
            status_code=201,
        )
        assert data["image"]["url"].startswith("http://example.com/media/test/")
        assert data["image"]["public_id"].startswith("test/")

    def test_category_json_image_object_still_works(self, admin_client):
        data = success_data(
            admin_client.post(
                self.URL,
                {
                    "name": "JSON Hats",
                    "image": {"url": "https://res.cloudinary.com/demo/image/upload/v1/shop/x.png"},
                },
                format="json",
            ),
            status_code=201,
        )
        assert data["image"]["url"] == "http://testserver/media/shop/x"
        assert data["image"]["public_id"] == "shop/x"

    def test_category_multipart_rejects_non_image(self, admin_client, tmp_path):
        bad = SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png")
        response = _post_multipart(
            admin_client, self.URL, {"name": "Bad", "image": bad}, tmp_path
        )
        assert response.status_code == 400
        assert "image" in response.data["errors"]

    def test_category_json_file_ref_rejected(self, admin_client):
        response = admin_client.post(
            self.URL, {"name": "Bad", "image": {"file": "missing"}}, format="json"
        )
        assert response.status_code == 400
        assert "multipart/form-data" in str(response.data["errors"])


class TestPavImageUpload:
    URL = "/api/v1/admin/product-attribute-values/"

    def test_pav_multipart_images(
        self, admin_client, product, color_attr, grey, tmp_path
    ):
        data = success_data(
            _post_multipart(
                admin_client,
                self.URL,
                {
                    "product": str(product.id),
                    "attribute": str(color_attr.id),
                    "attribute_value": str(grey.id),
                    "feature_image": _image_file("feature.png"),
                    "additional_images": [_image_file("a1.png"), _image_file("a2.png")],
                },
                tmp_path,
            ),
            status_code=201,
        )
        assert data["feature_image"]["url"].startswith("http://example.com/media/test/")
        assert len(data["additional_images"]) == 2
        assert all(
            item["url"].startswith("http://example.com/media/test/")
            for item in data["additional_images"]
        )

    def test_pav_multipart_requires_image_enforced(
        self, admin_client, product, color_attr, grey, tmp_path
    ):
        response = _post_multipart(
            admin_client,
            self.URL,
            {
                "product": str(product.id),
                "attribute": str(color_attr.id),
                "attribute_value": str(grey.id),
            },
            tmp_path,
        )
        assert response.status_code == 400
        assert "feature_image" in response.data["errors"]


class TestNestedMultipartUpload:
    URL = "/api/v1/admin/products/"

    def _payload(
        self, product_model, category, color_attr, size_attr, grey, size_40
    ):
        return {
            "name": "Multipart Slippers",
            "model": str(product_model.id),
            "gender": "UNISEX",
            "category": str(category.id),
            "attribute_values": json.dumps(
                [
                    {
                        "key": "grey",
                        "attribute": str(color_attr.id),
                        "attribute_value": str(grey.id),
                        "feature_image": {"file": "grey-img", "title": "Grey swatch"},
                    },
                    {
                        "key": "40",
                        "attribute": str(size_attr.id),
                        "attribute_value": str(size_40.id),
                    },
                ]
            ),
            "variants": json.dumps(
                [
                    {
                        "price": "5995.00",
                        "options": [{"key": "grey"}, {"key": "40"}],
                    }
                ]
            ),
        }

    def test_nested_multipart_product(
        self,
        admin_client,
        tmp_path,
        product_model,
        category,
        color_attr,
        size_attr,
        grey,
        size_40,
    ):
        from apps.catalog.models import ProductAttributeValue, ProductVariant

        payload = self._payload(
            product_model, category, color_attr, size_attr, grey, size_40
        )
        payload["grey-img"] = _image_file("grey.png")
        data = status_data(
            _post_multipart(admin_client, self.URL, payload, tmp_path),
            status_code=201,
        )
        pav = ProductAttributeValue.objects.get(
            product_id=data["id"], attribute_value=grey
        )
        assert pav.feature_image.url.startswith("/media/test/")
        assert pav.feature_image_title == "Grey swatch"
        assert ProductVariant.objects.filter(product_id=data["id"]).count() == 1

    def test_missing_file_part_rejected(
        self,
        admin_client,
        tmp_path,
        product_model,
        category,
        color_attr,
        size_attr,
        grey,
        size_40,
    ):
        payload = self._payload(
            product_model, category, color_attr, size_attr, grey, size_40
        )
        response = _post_multipart(admin_client, self.URL, payload, tmp_path)
        assert response.status_code == 400
        assert "grey-img" in str(response.data["errors"])

    def test_invalid_json_rejected(self, admin_client, tmp_path):
        response = _post_multipart(
            admin_client,
            self.URL,
            {"name": "Bad", "attribute_values": "[not-json"},
            tmp_path,
        )
        assert response.status_code == 400
        assert "valid JSON" in str(response.data["errors"])
