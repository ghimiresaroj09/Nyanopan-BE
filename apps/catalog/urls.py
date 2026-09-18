"""Public catalog URLs (mounted at /api/v1/).

Also hosts the tab-2 variant-values endpoint at its exact frontend path
(staff-only despite living outside /api/v1/admin/).
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.public import (
    AttributePublicViewSet,
    CategoryPublicViewSet,
    ProductModelPublicViewSet,
    ProductPublicViewSet,
)
from .views.variant_images import (
    ProductVariantImageDetailView,
    ProductVariantImagesView,
)
from .views.variant_values import ProductVariantValuesView

router = DefaultRouter()
router.register("categories", CategoryPublicViewSet, basename="public-category")
router.register("products", ProductPublicViewSet, basename="public-product")
router.register("product-models", ProductModelPublicViewSet, basename="public-product-model")
router.register("attributes", AttributePublicViewSet, basename="public-attribute")

urlpatterns = router.urls + [
    # Trailing-slash and bare variants of the same endpoint.
    path(
        "productvarientvalues/<uuid:product_id>/",
        ProductVariantValuesView.as_view(),
        name="product-variant-values",
    ),
    path(
        "productvarientvalues/<uuid:product_id>",
        ProductVariantValuesView.as_view(),
    ),
    path(
        "productvarientimages/<uuid:product_id>/",
        ProductVariantImagesView.as_view(),
        name="product-variant-images",
    ),
    path(
        "productvarientimages/<uuid:product_id>",
        ProductVariantImagesView.as_view(),
    ),
    path(
        "productvarientimages/<uuid:product_id>/images/<uuid:image_id>/",
        ProductVariantImageDetailView.as_view(),
        name="product-variant-image-detail",
    ),
    path(
        "productvarientimages/<uuid:product_id>/images/<uuid:image_id>",
        ProductVariantImageDetailView.as_view(),
    ),
]
