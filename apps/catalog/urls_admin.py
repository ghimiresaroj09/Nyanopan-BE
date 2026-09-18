"""Admin catalog URLs (mounted at /api/v1/admin/)."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.admin import (
    AdminAttributeValueViewSet,
    AdminAttributeViewSet,
    AdminCategoryViewSet,
    AdminProductAttributeValueViewSet,
    AdminProductModelViewSet,
    AdminProductViewSet,
    AdminVariantOptionViewSet,
    AdminVariantViewSet,
    ImageDeleteView,
    ImageUploadView,
)

router = DefaultRouter()
router.register("categories", AdminCategoryViewSet, basename="admin-category")
router.register("product-models", AdminProductModelViewSet, basename="admin-product-model")
router.register("products", AdminProductViewSet, basename="admin-product")
router.register("attributes", AdminAttributeViewSet, basename="admin-attribute")
router.register(
    "attribute-values", AdminAttributeValueViewSet, basename="admin-attribute-value"
)
router.register(
    "product-attribute-values",
    AdminProductAttributeValueViewSet,
    basename="admin-product-attribute-value",
)
router.register("variants", AdminVariantViewSet, basename="admin-variant")
router.register(
    "variant-options", AdminVariantOptionViewSet, basename="admin-variant-option"
)

urlpatterns = [
    path("images/upload/", ImageUploadView.as_view(), name="admin-image-upload"),
    path("images/delete/", ImageDeleteView.as_view(), name="admin-image-delete"),
    *router.urls,
]
