"""Tab-3 endpoints: GET/POST .../productvarientimages/{product_id}/ + DELETE .../images/{image_id}/."""

import uuid

import pytest
from django.test import TestCase, override_settings

from apps.catalog.models import ProductAttributeImage, ProductAttributeValue, ProductVariant
from apps.catalog.tests.test_image_uploads import _image_file
from apps.catalog.tests.test_simple_inputs import _data_uri
from conftest import make_pav, status_data

captureOnCommitCallbacks = TestCase.captureOnCommitCallbacks

pytestmark = pytest.mark.django_db


def _listing_url(product):
    return f"/api/v1/productvarientimages/{product.id}/"


def _image_url(product, image_id):
    return f"/api/v1/productvarientimages/{product.id}/images/{image_id}/"


class TestPermissions:
    def test_unauthenticated_denied(self, api_client, product):
        assert api_client.get(_listing_url(product)).status_code == 401
        assert api_client.post(_listing_url(product), {}).status_code == 401

    def test_non_staff_denied(self, plain_client, product):
        response = plain_client.get(_listing_url(product))
        assert response.status_code == 403
        assert response.data["success"] is False

    def test_unknown_product_404(self, admin_client):
        assert (
            admin_client.get(f"/api/v1/productvarientimages/{uuid.uuid4()}/").status_code
            == 404
        )


class TestGetListing:
    def test_grouped_values_with_images(self, admin_client, product_full):
        response = admin_client.get(_listing_url(product_full))
        assert response.status_code == 200
        assert set(response.data) == {"status", "message", "statusCode", "data"}
        assert response.data["message"] == "ProductVarientImages retrieved successfully"
        assert response.data["statusCode"] == 200

        groups = response.data["data"]["attributes"]
        assert [g["attribute"]["name"] for g in groups] == ["Color", "Size"]
        color = groups[0]
        assert set(color) == {"attribute", "values"}
        assert color["attribute"]["object"] == "attribute"
        assert [v["value"]["name"] for v in color["values"]] == ["Grey", "Blue"]

        grey = color["values"][0]
        assert set(grey) == {
            "id", "value", "is_active", "feature_image", "additional_images",
        }
        uuid.UUID(str(grey["id"]))
        assert grey["value"]["object"] == "attributevalueitem"
        assert grey["feature_image"]["url"].endswith("shop/grey-main")
        assert "public_id" not in grey["feature_image"]
        assert len(grey["additional_images"]) == 1
        gallery = grey["additional_images"][0]
        assert set(gallery) == {"id", "url", "title", "caption", "alt", "sort_order"}
        assert gallery["sort_order"] == 0
        assert gallery["url"].endswith("shop/grey-side")

        size_40 = next(
            v for g in groups for v in g["values"] if v["value"]["name"] == "40"
        )
        assert size_40["feature_image"] is None
        assert size_40["additional_images"] == []

    def test_only_this_products_values(
        self, admin_client, product_full, admin_user, category, product_model,
        color_attr, grey,
    ):
        from apps.catalog.models import Product

        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        make_pav(other, color_attr, grey)
        data = status_data(admin_client.get(_listing_url(product_full)))
        names = [v["value"]["name"] for g in data["attributes"] for v in g["values"]]
        assert sorted(names) == ["40", "41", "Blue", "Grey"]
        data = status_data(admin_client.get(_listing_url(other)))
        assert [g["attribute"]["name"] for g in data["attributes"]] == ["Color"]

    def test_empty_product(self, admin_client, product):
        assert status_data(admin_client.get(_listing_url(product))) == {"attributes": []}

    def test_bare_path_works(self, admin_client, product_full):
        data = status_data(
            admin_client.get(f"/api/v1/productvarientimages/{product_full.id}")
        )
        assert len(data["attributes"]) == 2


class TestUpload:
    def test_json_data_uri_sets_feature_and_appends_gallery(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    _listing_url(product),
                    {
                        "value": str(pav.id),
                        "feature_image": {
                            "file": _data_uri(color="red"),
                            "title": "Red",
                            "alt": "Red swatch",
                        },
                        "additional_images": [
                            {"file": _data_uri(color="blue"), "alt": "Side"}
                        ],
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert set(data) == {
            "id", "attribute", "value", "is_active",
            "feature_image", "additional_images",
        }
        assert data["attribute"]["name"] == "Color"
        assert data["value"]["name"] == "Grey"
        assert data["feature_image"]["url"].startswith("http://testserver/media/")
        assert data["feature_image"]["title"] == "Red"
        assert len(data["additional_images"]) == 1
        assert data["additional_images"][0]["sort_order"] == 0
        pav.refresh_from_db()
        assert pav.feature_image.name
        assert (tmp_path / pav.feature_image.name).is_file()
        gallery = pav.additional_images.get()
        assert (tmp_path / gallery.image.name).is_file()

    def test_multipart_files_append_repeated_parts(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    _listing_url(product),
                    {
                        "value": str(pav.id),
                        "feature_image": _image_file("feat.png"),
                        "additional_images": [_image_file("a.png"), _image_file("b.png")],
                    },
                    format="multipart",
                ),
                status_code=201,
            )
        assert data["feature_image"]["url"].startswith("http://testserver/media/")
        assert [g["sort_order"] for g in data["additional_images"]] == [0, 1]
        assert pav.additional_images.count() == 2

    def test_second_upload_appends_after_existing(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        url = _listing_url(product)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            first = status_data(
                admin_client.post(
                    url,
                    {
                        "value": str(pav.id),
                        "additional_images": [{"file": _data_uri(color="red")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
            second = status_data(
                admin_client.post(
                    url,
                    {
                        "value": str(pav.id),
                        "additional_images": [{"file": _data_uri(color="blue")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert len(first["additional_images"]) == 1
        assert [g["sort_order"] for g in second["additional_images"]] == [0, 1]
        assert second["additional_images"][0]["id"] == first["additional_images"][0]["id"]

    def test_null_clears_featured_and_cleans_file(
        self, admin_client, tmp_path, product, size_attr, size_40
    ):
        pav = make_pav(product, size_attr, size_40)
        url = _listing_url(product)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            status_data(
                admin_client.post(
                    url,
                    {
                        "value": str(pav.id),
                        "feature_image": {"file": _data_uri(color="red")},
                    },
                    format="json",
                ),
                status_code=201,
            )
            pav.refresh_from_db()
            old_name = pav.feature_image.name
            assert (tmp_path / old_name).is_file()
            with captureOnCommitCallbacks(execute=True):
                data = status_data(
                    admin_client.post(
                        url, {"value": str(pav.id), "feature_image": None}, format="json"
                    ),
                    status_code=201,
                )
        assert data["feature_image"] is None
        assert not (tmp_path / old_name).exists()

    def test_replace_featured_cleans_old_file(
        self, admin_client, tmp_path, product, size_attr, size_40
    ):
        pav = make_pav(product, size_attr, size_40)
        url = _listing_url(product)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            with captureOnCommitCallbacks(execute=True):
                status_data(
                    admin_client.post(
                        url,
                        {
                            "value": str(pav.id),
                            "feature_image": {"file": _data_uri(color="red")},
                        },
                        format="json",
                    ),
                    status_code=201,
                )
                pav.refresh_from_db()
                old_name = pav.feature_image.name
                status_data(
                    admin_client.post(
                        url,
                        {
                            "value": str(pav.id),
                            "feature_image": {"file": _data_uri(color="blue")},
                        },
                        format="json",
                    ),
                    status_code=201,
                )
        pav.refresh_from_db()
        assert pav.feature_image.name != old_name
        assert not (tmp_path / old_name).exists()

    def test_neither_field_rejected(self, admin_client, product, color_attr, grey):
        pav = make_pav(product, color_attr, grey)
        response = admin_client.post(
            _listing_url(product), {"value": str(pav.id)}, format="json"
        )
        assert response.status_code == 400

    def test_value_must_belong_to_product(
        self, admin_client, product, category, product_model, color_attr, grey
    ):
        from apps.catalog.models import Product

        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        foreign = make_pav(other, color_attr, grey)
        response = admin_client.post(
            _listing_url(product),
            {"value": str(foreign.id), "feature_image": None},
            format="json",
        )
        assert response.status_code == 400
        assert "not used on this product" in str(response.data["errors"])
        response = admin_client.post(
            _listing_url(product),
            {"value": str(uuid.uuid4()), "feature_image": None},
            format="json",
        )
        assert response.status_code == 400

    def test_requires_image_allows_gallery_first_blocks_featured_clear(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        assert color_attr.requires_image is True
        pav = make_pav(product, color_attr, grey)
        url = _listing_url(product)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            # Gallery-only upload succeeds while featured is still empty.
            data = status_data(
                admin_client.post(
                    url,
                    {
                        "value": str(pav.id),
                        "additional_images": [{"file": _data_uri(color="red")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
            assert len(data["additional_images"]) == 1
            # Clearing featured on an image-requiring attribute is rejected.
            status_data(
                admin_client.post(
                    url,
                    {
                        "value": str(pav.id),
                        "feature_image": {"file": _data_uri(color="blue")},
                    },
                    format="json",
                ),
                status_code=201,
            )
            response = admin_client.post(
                url, {"value": str(pav.id), "feature_image": None}, format="json"
            )
            assert response.status_code == 400
            assert "feature_image" in str(response.data["errors"])

    def test_non_image_file_rejected(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        from django.core.files.uploadedfile import SimpleUploadedFile

        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            response = admin_client.post(
                _listing_url(product),
                {
                    "value": str(pav.id),
                    "feature_image": SimpleUploadedFile(
                        "note.txt", b"not an image", content_type="text/plain"
                    ),
                },
                format="multipart",
            )
        assert response.status_code == 400

    def test_bare_path_upload_works(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    f"/api/v1/productvarientimages/{product.id}",
                    {
                        "value": str(pav.id),
                        "feature_image": {"file": _data_uri(color="red")},
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert data["feature_image"]["url"].startswith("http://testserver/media/")


class TestDeleteGalleryImage:
    def test_delete_removes_row_and_file(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    _listing_url(product),
                    {
                        "value": str(pav.id),
                        "additional_images": [{"file": _data_uri(color="red")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
            image_id = data["additional_images"][0]["id"]
            name = pav.additional_images.get(pk=image_id).image.name
            assert (tmp_path / name).is_file()
            with captureOnCommitCallbacks(execute=True):
                response = admin_client.delete(_image_url(product, image_id))
        assert response.status_code == 200
        assert response.data == {
            "status": "success",
            "message": "ProductVarientImage deleted successfully",
            "statusCode": 200,
            "data": {},
        }
        assert not ProductAttributeImage.objects.filter(pk=image_id).exists()
        assert not (tmp_path / name).exists()

    def test_delete_foreign_or_unknown_image_404(
        self, admin_client, product, product_full, category, product_model
    ):
        from apps.catalog.models import Product

        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        foreign_id = ProductAttributeImage.objects.filter(
            product_attribute_value__product=product_full
        ).values_list("id", flat=True)[0]
        assert admin_client.delete(_image_url(other, foreign_id)).status_code == 404
        assert admin_client.delete(_image_url(other, uuid.uuid4())).status_code == 404

    def test_delete_permissions(self, api_client, plain_client, product):
        assert (
            api_client.delete(_image_url(product, uuid.uuid4())).status_code == 401
        )
        assert (
            plain_client.delete(_image_url(product, uuid.uuid4())).status_code == 403
        )

    def test_bare_path_delete_works(
        self, admin_client, tmp_path, product, color_attr, grey
    ):
        pav = make_pav(product, color_attr, grey)
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    _listing_url(product),
                    {
                        "value": str(pav.id),
                        "additional_images": [{"file": _data_uri(color="red")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
            image_id = data["additional_images"][0]["id"]
            response = admin_client.delete(
                f"/api/v1/productvarientimages/{product.id}/images/{image_id}"
            )
        assert response.status_code == 200


class TestSharedAcrossVariants:
    def test_variants_sharing_a_value_resolve_its_images(
        self, admin_client, tmp_path, product_full
    ):
        """Red M and Red S show the same pictures: images live on the value."""
        grey_pav = ProductAttributeValue.objects.get(
            product=product_full, attribute_value__name="Grey"
        )
        variants = list(
            ProductVariant.objects.filter(
                options__product_attribute_value=grey_pav
            ).distinct()
        )
        assert {v.sku for v in variants} == {"CELSI-GREY-40", "CELSI-GREY-41"}
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    _listing_url(product_full),
                    {
                        "value": str(grey_pav.id),
                        "feature_image": {"file": _data_uri(color="red")},
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert data["feature_image"]["url"].startswith("http://testserver/media/")
        grey_pav.refresh_from_db()
        for variant in variants:
            resolved = variant.options.get(
                product_attribute_value=grey_pav
            ).product_attribute_value
            assert resolved.feature_image.name == grey_pav.feature_image.name
