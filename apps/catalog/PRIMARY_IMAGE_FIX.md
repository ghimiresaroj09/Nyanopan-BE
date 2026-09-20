# Primary Image Fix - Product List

## Issue
In product list endpoints (GET all products), the `primary_image` was incorrectly showing the **attribute value's feature image** instead of the **product's feature image**.

This issue only affected:
- `GET /api/v1/products/` (public list)
- `GET /api/v1/admin/products/` (admin list)

Detail endpoints were working correctly:
- `GET /api/v1/products/{slug}/` (public detail)
- `GET /api/v1/admin/products/{id}/` (admin detail)

---

## Root Cause

The `get_primary_image()` method in both list serializers was only checking attribute value images, not the product's own `feature_image` field.

### Before (Incorrect)
```python
def get_primary_image(self, obj):
    # Only looked at attribute value images
    pav = obj.attribute_values.filter(...).first()
    if not pav or not pav.feature_image.name:
        return None
    return pav.feature_image  # ❌ Wrong - returns attribute image
```

### After (Correct)
```python
def get_primary_image(self, obj):
    # First check product's feature_image
    if obj.feature_image and obj.feature_image.name:
        return obj.feature_image  # ✅ Correct - returns product image
    
    # Fallback to attribute value image if product has none
    pav = obj.attribute_values.filter(...).first()
    if not pav or not pav.feature_image.name:
        return None
    return pav.feature_image  # ✅ Fallback
```

---

## Fix Applied

### 1. Public List Serializer (`ProductListSerializer`)

**File:** `apps/catalog/serializers/public.py`

**Changes:**
```python
@extend_schema_field(IMAGE_SCHEMA)
def get_primary_image(self, obj):
    # NEW: Check product's feature_image first
    if obj.feature_image and obj.feature_image.name:
        return {
            "url": _absolute_media_url(self.context, obj.feature_image.url),
            "title": obj.feature_image_title or "",
            "caption": obj.feature_image_caption or "",
            "alt": obj.feature_image_alt or "",
        }
    
    # Fallback to attribute value feature image
    images = getattr(obj, "prefetched_images", None)
    if images is None:
        pav = (
            obj.attribute_values.filter(
                is_active=True,
                attribute__is_active=True,
                attribute_value__is_active=True,
            )
            .exclude(feature_image="")
            .order_by("-attribute__requires_image", "id")
            .first()
        )
    else:
        pav = images[0] if images else None
    
    if not pav or not pav.feature_image.name:
        return None
    
    return {
        "url": _absolute_media_url(self.context, pav.feature_image.url),
        "title": pav.feature_image_title or "",
        "caption": pav.feature_image_caption or "",
        "alt": pav.feature_image_alt or "",
    }
```

### 2. Admin List Serializer (`ProductAdminListSerializer`)

**File:** `apps/catalog/serializers/admin.py`

**Changes:**
```python
@extend_schema_field(IMAGE_SCHEMA)
def get_primary_image(self, obj):
    # NEW: Check product's feature_image first
    if obj.feature_image and obj.feature_image.name:
        return ImageObjectField(prefix="feature_image").to_representation(obj)
    
    # Fallback to attribute value feature image
    images = getattr(obj, "prefetched_images", None)
    if images is None:
        pav = (
            obj.attribute_values.filter(
                is_active=True,
                attribute__is_active=True,
                attribute_value__is_active=True,
            )
            .exclude(feature_image="")
            .order_by("-attribute__requires_image", "id")
            .first()
        )
    else:
        pav = images[0] if images else None
    
    if not pav or not pav.feature_image.name:
        return None
    
    return ImageObjectField(prefix="feature_image").to_representation(pav)
```

---

## Image Priority Logic

The fix implements this priority:

1. **Product's `feature_image`** (primary)
   - If product has its own feature_image uploaded
   - This is the main product image

2. **Attribute Value's `feature_image`** (fallback)
   - If product has no feature_image
   - Uses first attribute value's image (e.g., Color's image)
   - Prioritizes attributes with `requires_image=True`

3. **None** (no image)
   - If neither exists

---

## Product Model Fields

For reference, the Product model has:

```python
class Product(TimeStampedModel, SluggedModelMixin):
    # Main product image
    feature_image = models.ImageField(
        upload_to=product_feature_image_path,
        storage=image_storage,
        validators=[validate_image_upload],
        blank=True,
        help_text="Main product image shown in listings and detail views.",
    )
    feature_image_title = models.CharField(max_length=255, blank=True, default="")
    feature_image_caption = models.CharField(max_length=255, blank=True, default="")
    feature_image_alt = models.CharField(max_length=255, blank=True, default="")
```

---

## Expected Behavior

### Scenario 1: Product has feature_image
```json
{
  "id": "uuid",
  "name": "Celsi Wool Felt Slippers",
  "primary_image": {
    "url": "https://res.cloudinary.com/.../product-main.jpg",  // ✅ Product's image
    "title": "Celsi Slippers Main",
    "caption": "...",
    "alt": "..."
  }
}
```

### Scenario 2: Product has no feature_image, but has attribute images
```json
{
  "id": "uuid",
  "name": "Another Product",
  "primary_image": {
    "url": "https://res.cloudinary.com/.../grey-color.jpg",  // ✅ Fallback to attribute
    "title": "Grey Color Variant",
    "caption": "...",
    "alt": "..."
  }
}
```

### Scenario 3: No images at all
```json
{
  "id": "uuid",
  "name": "Product Without Images",
  "primary_image": null  // ✅ No image available
}
```

---

## Testing

To verify the fix works:

### 1. Test Product List
```bash
curl http://localhost:8000/api/v1/products/
```

Check that `primary_image.url` points to the product's feature_image.

### 2. Test Admin Product List
```bash
curl http://localhost:8000/api/v1/admin/products/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Check that `primary_image.url` and `primary_image.name` are correct.

### 3. Compare with Detail View
```bash
# List view
curl http://localhost:8000/api/v1/products/ | jq '.[0].primary_image'

# Detail view
curl http://localhost:8000/api/v1/products/celsi-wool-felt-slippers/ | jq '.feature_image'
```

Both should show the same product feature_image.

---

## Files Modified

1. **apps/catalog/serializers/public.py**
   - Updated `ProductListSerializer.get_primary_image()`
   - Added product feature_image check first
   - Kept attribute image as fallback

2. **apps/catalog/serializers/admin.py**
   - Updated `ProductAdminListSerializer.get_primary_image()`
   - Added product feature_image check first
   - Kept attribute image as fallback

---

## Impact

### Fixed
✅ Product list now shows correct product feature image  
✅ Admin product list now shows correct product feature image  
✅ Fallback to attribute images still works  
✅ No breaking changes to API response structure  

### Unchanged
✅ Detail endpoints already working correctly  
✅ Response format unchanged  
✅ All existing frontend code compatible  

---

## Summary

**Before:** List endpoints returned attribute value images instead of product images  
**After:** List endpoints correctly return product feature_image (with attribute image fallback)  
**Result:** Consistent image display across list and detail views  

The fix ensures product listings show the correct main product image! 🎉
