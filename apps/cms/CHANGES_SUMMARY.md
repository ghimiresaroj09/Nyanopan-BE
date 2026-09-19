# CMS Image Upload Changes - Summary

## What Changed

### Database Schema
**Migration:** `0007_convert_images_to_imagefield.py`

Changed image fields from `CharField` (URL strings) to `ImageField` (binary uploads):

| Model | Field | Before | After |
|-------|-------|--------|-------|
| TeamMember | `image` | CharField(500) | ImageField |
| OurStory | `section1_image` | CharField(500) | ImageField |
| OurStory | `section2_image` | CharField(500) | ImageField |
| StorySubsection | `image` | CharField(500) | ImageField |
| SustainabilitySection | `image` | CharField(500) | ImageField |

**Storage:** All images use Cloudinary storage with automatic validation
**Upload paths:** Organized under `ecommerce/cms/` folder structure

### API Changes

#### Added MultiPart Support
Updated views to accept `multipart/form-data` for binary file uploads:
- `OurMakersAdminView` - parser_classes added
- `TeamMemberAdminViewSet` - parser_classes added  
- `OurStoryAdminView` - parser_classes added
- `OurSustainabilityAdminView` - parser_classes added

#### Parsers Enabled
All admin views now support:
- `JSONParser` - For JSON payloads (existing behavior)
- `MultiPartParser` - For binary file uploads
- `FormParser` - For form-encoded data

## How to Use

### Simple Fields (Direct Binary Upload)
Team members, Story section1/2 images - just attach file directly:

```javascript
const formData = new FormData();
formData.append('name', 'John Doe');
formData.append('image', fileInput.files[0]);  // Binary file

fetch('/api/v1/admin/team-members/', {
  method: 'POST',
  body: formData
});
```

### Nested Arrays (JSON with URLs)
For subsections/sections in nested updates - use JSON with image URLs:

```javascript
// Option 1: Use existing Cloudinary URL
const data = {
  section3_subsections: [
    {
      title: 'New Section',
      image: 'https://res.cloudinary.com/your-cloud/image/upload/v123/file.jpg',
      description: 'Content here'
    }
  ]
};

fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

## Backward Compatibility

✅ **Existing URL strings still work** - Django ImageField accepts URL strings
✅ **No data migration needed** - existing data remains valid
✅ **Gradual migration** - mix URLs and binary uploads

## Files Modified

1. **apps/cms/models.py**
   - Added image path helper functions
   - Converted 5 CharField fields to ImageField
   - Added validators and storage configuration

2. **apps/cms/views.py**
   - Added MultiPartParser, FormParser imports
   - Added parser_classes to 4 admin views

3. **apps/cms/migrations/0007_convert_images_to_imagefield.py**
   - Schema migration (auto-generated)

## New Documentation

1. **IMAGE_UPLOAD_GUIDE.md** - Complete guide for frontend developers
2. **CHANGES_SUMMARY.md** - This file

## Testing Checklist

- [ ] Upload image to team member (binary)
- [ ] Upload image to Our Story section1 (binary)
- [ ] Update Our Story with nested subsections (JSON + URLs)
- [ ] Update Sustainability with nested sections (JSON + URLs)
- [ ] Verify existing URLs still work
- [ ] Check image URLs in API responses
- [ ] Verify images appear in Django admin
- [ ] Test with invalid file types (should reject)
- [ ] Test with oversized files (should reject)

## Next Steps

### For Frontend Developers
1. Read `IMAGE_UPLOAD_GUIDE.md` for complete examples
2. Update forms to handle file uploads for simple fields
3. For nested updates, implement URL-based approach or pre-upload images

### For Backend Developers
Optional enhancements:
1. Create dedicated `/upload-image/` endpoint for pre-uploading images
2. Add image optimization/resizing logic
3. Add more detailed validation rules (dimensions, aspect ratio)
4. Consider adding image variants/thumbnails

## Migration Path

### Current Setup (Post-Change)
- All image fields are now `ImageField`
- Accept both binary uploads and URL strings
- Stored in Cloudinary with organized paths

### If You Need to Rollback
```bash
# Rollback migration
python manage.py migrate cms 0006

# Note: New binary uploads will be lost, but URL strings remain
```

## Configuration Requirements

Ensure `.env` contains:
```
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
CLOUDINARY_UPLOAD_FOLDER=ecommerce
```

Images will be stored under:
- `ecommerce/cms/team-members/` - Team member photos
- `ecommerce/cms/story/` - Story section images
- `ecommerce/cms/story-subsections/` - Story subsection images
- `ecommerce/cms/sustainability/` - Sustainability section images
