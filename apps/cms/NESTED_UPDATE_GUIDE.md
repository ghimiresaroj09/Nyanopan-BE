# CMS Nested Updates Guide

## Overview
The Our Story and Our Sustainability pages now support managing nested sections directly through their main update endpoints. You no longer need separate APIs for subsections/sections.

## Our Story - Managing Subsections

### Endpoint
```
PATCH /api/v1/admin/our-story/
```

### Update with Nested Subsections
```json
{
  "title": "Our Story",
  "description": "Learn about our journey",
  "section1_title": "The Beginning",
  "section1_description": "How we started...",
  "section1_image": "https://example.com/image1.jpg",
  "section2_title": "Our Growth",
  "section2_description": "How we expanded...",
  "section2_image": "https://example.com/image2.jpg",
  "section3_title": "Our Team",
  "section3_subsections": [
    {
      "id": 1,
      "title": "Updated Subsection",
      "description": "Updated content",
      "image": "https://example.com/updated.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "title": "New Subsection",
      "description": "Brand new content",
      "image": "https://example.com/new.jpg",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

### Rules for Subsections
- **With `id` field**: Updates existing subsection
- **Without `id` field**: Creates new subsection
- **Omitted items**: Not automatically deleted (manual deletion required via admin or database)

## Our Sustainability - Managing Sections

### Endpoint
```
PATCH /api/v1/admin/our-sustainability/
```

### Update with Nested Sections
```json
{
  "title": "Our Sustainability",
  "description": "Our commitment to the environment",
  "sections": [
    {
      "id": 5,
      "title": "Updated Section",
      "description": "Updated sustainability info",
      "image": "https://example.com/updated-sustainability.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "title": "New Initiative",
      "description": "Our latest green initiative",
      "image": "https://example.com/new-initiative.jpg",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

### Rules for Sections
- **With `id` field**: Updates existing section
- **Without `id` field**: Creates new section
- **Omitted items**: Not automatically deleted (manual deletion required)

## Removed Endpoints
The following endpoints have been removed:
- ❌ `/api/v1/admin/story-subsections/` (use `/api/v1/admin/our-story/` instead)
- ❌ `/api/v1/admin/sustainability-sections/` (use `/api/v1/admin/our-sustainability/` instead)

## Benefits
1. **Single API call**: Update page and all nested items in one request
2. **Atomic updates**: All changes succeed or fail together
3. **Simpler frontend**: No need to manage multiple API endpoints
4. **Consistent patterns**: Same approach for both Story and Sustainability pages

## Example: Complete Update Flow

```javascript
// Fetch current data
const response = await fetch('/api/v1/admin/our-story/');
const data = await response.json();

// Modify nested subsections
data.section3_subsections[0].title = "Updated Title"; // Update existing
data.section3_subsections.push({
  title: "New Subsection",
  description: "New content",
  image: "https://example.com/new.jpg",
  sort_order: 3,
  is_active: true
}); // Add new

// Send back in one request
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

## Notes
- Auto-deletion of omitted items is disabled by default to prevent accidental data loss
- If you need to delete subsections/sections, use Django admin or direct database access
- All nested items require proper foreign key relationships (automatically handled on create)
