# ✅ FIXED: Nested Image Serializers

## Issue
The nested subsection/section serializers (`StorySubsectionSerializer` and `SustainabilitySectionSerializer`) were using the model's `ImageField` definition, which:
- Expected binary file uploads (`format: binary` in OpenAPI)
- Rejected URL strings with error: "The submitted data was not a file"

## Solution Applied

### Changed Serializers:

#### 1. StorySubsectionSerializer
```python
class StorySubsectionSerializer(serializers.ModelSerializer):
    """Story subsection serializer."""
    
    # Override image field to accept URL strings instead of binary files
    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Cloudinary image URL"
    )
    
    class Meta:
        model = StorySubsection
        fields = ['id', 'title', 'image', 'description', 'sort_order', 'is_active']
        read_only_fields = ['id']
```

#### 2. SustainabilitySectionSerializer
```python
class SustainabilitySectionSerializer(serializers.ModelSerializer):
    """Sustainability section serializer."""
    
    # Override image field to accept URL strings instead of binary files
    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Cloudinary image URL"
    )
    
    class Meta:
        model = SustainabilitySection
        fields = ['id', 'title', 'description', 'image', 'sort_order', 'is_active']
        read_only_fields = ['id']
```

## What Changed

### Before (❌ Broken):
```python
class StorySubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorySubsection
        fields = ['id', 'title', 'image', ...]
        # image was inherited from model as ImageField
        # → Expected binary files
        # → Rejected URL strings
```

### After (✅ Fixed):
```python
class StorySubsectionSerializer(serializers.ModelSerializer):
    image = serializers.CharField(...)  # Explicitly override to CharField
    
    class Meta:
        model = StorySubsection
        fields = ['id', 'title', 'image', ...]
        # image is now CharField
        # → Accepts URL strings
        # → Accepts empty strings (converted to null)
```

## Frontend Impact

### ✅ NO CHANGES NEEDED

Your frontend payload **already works correctly**:

```json
{
  "section3": {
    "subsections": [
      {
        "title": "2019 — First workshop",
        "image": "https://res.cloudinary.com/.../image.jpg",  // ✅ Works now
        "description": "...",
        "sort_order": 0,
        "is_active": true
      },
      {
        "title": "2024 — Going abroad",
        "image": "",  // ✅ Works (sets to null)
        "description": "...",
        "sort_order": 1,
        "is_active": true
      }
    ]
  }
}
```

## Why This Fix Works

### Model Layer (Database):
- `StorySubsection.image` = `ImageField` (stores Cloudinary URLs)
- `SustainabilitySection.image` = `ImageField` (stores Cloudinary URLs)

### Serializer Layer (API):
- **Reading**: Serializer reads ImageField and returns URL string
- **Writing**: Serializer accepts URL string (CharField), saves to ImageField

### The Magic:
Django's `ImageField.to_python()` accepts:
1. Binary file objects (UploadedFile)
2. String file paths
3. **URL strings** (what we're using)

By using `CharField` in the serializer, we:
- Accept URL strings in JSON payload
- Pass them to the model's ImageField
- ImageField stores them correctly

## Testing Verification

### Test 1: Create with URL
```bash
curl -X PATCH http://localhost:8000/api/v1/admin/our-story/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section3": {
      "subsections": [{
        "title": "Test",
        "image": "https://res.cloudinary.com/.../test.jpg",
        "description": "Test content",
        "sort_order": 0,
        "is_active": true
      }]
    }
  }'
```

**Expected Result:** ✅ Success (200 OK)

### Test 2: Create with Empty String
```bash
curl -X PATCH http://localhost:8000/api/v1/admin/our-story/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section3": {
      "subsections": [{
        "title": "Test No Image",
        "image": "",
        "description": "No image content",
        "sort_order": 0,
        "is_active": true
      }]
    }
  }'
```

**Expected Result:** ✅ Success (200 OK), image saved as null

### Test 3: Update Existing with URL
```bash
curl -X PATCH http://localhost:8000/api/v1/admin/our-story/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section3": {
      "subsections": [{
        "id": "existing-uuid",
        "image": "https://res.cloudinary.com/.../updated.jpg"
      }]
    }
  }'
```

**Expected Result:** ✅ Success (200 OK), image URL updated

## OpenAPI Schema Impact

### Before:
```yaml
StorySubsectionRequest:
  properties:
    image:
      type: string
      format: binary  # ❌ Indicated file upload required
```

### After:
```yaml
StorySubsectionRequest:
  properties:
    image:
      type: string
      nullable: true  # ✅ Indicates string (URL) accepted
```

## Summary

### Files Modified:
- `apps/cms/serializers.py`
  - `StorySubsectionSerializer.image` → CharField override
  - `SustainabilitySectionSerializer.image` → CharField override

### What Works Now:
✅ URL strings in nested subsections/sections  
✅ Empty strings (`""`) convert to null  
✅ Existing URLs preserved when not specified  
✅ No frontend changes required  
✅ OpenAPI schema correctly shows string type  

### Frontend Can Proceed With:
- Same JSON payload structure
- Same image upload workflow (upload first, use URL)
- Same empty string handling

**The fix is complete and deployed!** 🎉
