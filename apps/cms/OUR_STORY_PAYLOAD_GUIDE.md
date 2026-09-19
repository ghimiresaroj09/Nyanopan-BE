# Our Story API Payload Guide

## Endpoint
```
GET    /api/v1/our-story/              (Public - no auth)
GET    /api/v1/admin/our-story/        (Admin - requires auth)
PUT    /api/v1/admin/our-story/        (Admin - full update)
PATCH  /api/v1/admin/our-story/        (Admin - partial update)
```

---

## Response Structure (GET)

### Public Response
```json
{
  "success": true,
  "message": "Our Story page retrieved successfully.",
  "data": {
    "title": "Our Story",
    "description": "Learn about our journey and mission",
    "section1": {
      "title": "The Beginning",
      "description": "How we started our journey...",
      "image": "https://res.cloudinary.com/.../section1.jpg"
    },
    "section2": {
      "title": "Our Growth",
      "description": "How we expanded and evolved...",
      "image": "https://res.cloudinary.com/.../section2.jpg"
    },
    "section3": {
      "title": "Our Journey",
      "subsections": [
        {
          "title": "First Milestone",
          "image": "https://res.cloudinary.com/.../milestone1.jpg",
          "description": "Our first major achievement..."
        },
        {
          "title": "Second Milestone",
          "image": "https://res.cloudinary.com/.../milestone2.jpg",
          "description": "Expanding our vision..."
        }
      ]
    }
  }
}
```

### Admin Response
```json
{
  "success": true,
  "message": "Our Story page retrieved successfully.",
  "data": {
    "id": 1,
    "title": "Our Story",
    "description": "Learn about our journey and mission",
    "section1": {
      "title": "The Beginning",
      "description": "How we started our journey...",
      "image": "https://res.cloudinary.com/.../section1.jpg"
    },
    "section2": {
      "title": "Our Growth",
      "description": "How we expanded and evolved...",
      "image": "https://res.cloudinary.com/.../section2.jpg"
    },
    "section3": {
      "title": "Our Journey",
      "subsections": [
        {
          "id": "uuid-1",
          "title": "First Milestone",
          "image": "https://res.cloudinary.com/.../milestone1.jpg",
          "description": "Our first major achievement...",
          "sort_order": 1,
          "is_active": true
        },
        {
          "id": "uuid-2",
          "title": "Second Milestone",
          "image": "https://res.cloudinary.com/.../milestone2.jpg",
          "description": "Expanding our vision...",
          "sort_order": 2,
          "is_active": true
        }
      ]
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Update Payloads (PUT/PATCH)

### Method 1: JSON Payload (Recommended for Nested Updates)

Use this when updating text content and subsections with existing image URLs.

#### Update Main Content Only
```json
{
  "title": "Our Story",
  "description": "Updated main description"
}
```

#### Update Section 1 & 2 (Text Only)
```json
{
  "section1": {
    "title": "Updated Beginning",
    "description": "New description for section 1",
    "image": "https://res.cloudinary.com/.../existing-image.jpg"
  },
  "section2": {
    "title": "Updated Growth",
    "description": "New description for section 2",
    "image": "https://res.cloudinary.com/.../another-image.jpg"
  }
}
```

**Note:** When using nested JSON structure for sections, you must provide the full section object. The serializer uses `source='*'` mapping.

#### Alternative: Flat Structure for Sections
```json
{
  "section1_title": "Updated Beginning",
  "section1_description": "New description for section 1",
  "section1_image": "https://res.cloudinary.com/.../existing-image.jpg",
  "section2_title": "Updated Growth",
  "section2_description": "New description for section 2",
  "section2_image": "https://res.cloudinary.com/.../another-image.jpg"
}
```

**This flat structure is RECOMMENDED for updates** because it maps directly to model fields.

#### Update Section 3 with Subsections

**Update Existing Subsection:**
```json
{
  "section3_title": "Our Journey",
  "section3_subsections": [
    {
      "id": "uuid-1",
      "title": "Updated Milestone",
      "description": "Updated description",
      "image": "https://res.cloudinary.com/.../updated-image.jpg",
      "sort_order": 1,
      "is_active": true
    }
  ]
}
```

**Create New Subsection:**
```json
{
  "section3_subsections": [
    {
      "title": "New Milestone",
      "description": "Brand new subsection",
      "image": "https://res.cloudinary.com/.../new-image.jpg",
      "sort_order": 3,
      "is_active": true
    }
  ]
}
```

**Mix Update & Create:**
```json
{
  "section3_subsections": [
    {
      "id": "uuid-1",
      "title": "Updated First Milestone",
      "description": "Updated content",
      "image": "https://res.cloudinary.com/.../image1.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "title": "New Third Milestone",
      "description": "New content",
      "image": "https://res.cloudinary.com/.../image3.jpg",
      "sort_order": 3,
      "is_active": true
    }
  ]
}
```

**Full Page Update:**
```json
{
  "title": "Our Story",
  "description": "Complete page description",
  "section1_title": "The Beginning",
  "section1_description": "How we started...",
  "section1_image": "https://res.cloudinary.com/.../section1.jpg",
  "section2_title": "Our Growth",
  "section2_description": "How we expanded...",
  "section2_image": "https://res.cloudinary.com/.../section2.jpg",
  "section3_title": "Our Journey",
  "section3_subsections": [
    {
      "id": "uuid-1",
      "title": "First Milestone",
      "description": "First achievement",
      "image": "https://res.cloudinary.com/.../milestone1.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "title": "New Milestone",
      "description": "Latest achievement",
      "image": "https://res.cloudinary.com/.../milestone-new.jpg",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

---

### Method 2: Multipart/Form-Data (For Binary Image Uploads)

Use this when uploading new images for section1 or section2.

**Update Section 1 with New Image:**
```bash
curl -X PATCH https://api.example.com/api/v1/admin/our-story/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "section1_title=New Beginning" \
  -F "section1_description=Updated description" \
  -F "section1_image=@/path/to/new-image.jpg"
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('section1_title', 'New Beginning');
formData.append('section1_description', 'Updated description');
formData.append('section1_image', imageFile); // File from <input type="file">

// Optional: Update section 2 at the same time
formData.append('section2_title', 'New Growth');
formData.append('section2_image', imageFile2);

const response = await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Important:** Multipart updates work best for section1 and section2 images. For subsections with images, use JSON with URLs (see Method 1).

---

## Field Reference

### Root Level Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | read-only | Always 1 (singleton) |
| `title` | string | optional | Main page title (default: "Our Story") |
| `description` | text | optional | Main introduction text |
| `created_at` | datetime | read-only | Creation timestamp |
| `updated_at` | datetime | read-only | Last update timestamp |

### Section 1 & 2 Fields (Flat Structure)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `section1_title` | string | optional | Section 1 title |
| `section1_description` | text | optional | Section 1 content |
| `section1_image` | image/url | optional | Section 1 image (binary or URL) |
| `section2_title` | string | optional | Section 2 title |
| `section2_description` | text | optional | Section 2 content |
| `section2_image` | image/url | optional | Section 2 image (binary or URL) |

### Section 3 Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `section3_title` | string | optional | Section 3 title (default: "Our Journey") |
| `section3_subsections` | array | optional | Array of subsection objects |

### Subsection Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | uuid | conditional | Required for update, omit for create |
| `title` | string | required | Subsection title |
| `image` | url | optional | Image URL (Cloudinary) |
| `description` | text | required | Subsection content |
| `sort_order` | integer | optional | Display order (default: 0) |
| `is_active` | boolean | optional | Visibility status (default: true) |

---

## Common Workflows

### 1. Update Only Text (No Images)
```javascript
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Updated Story Title',
    section1_title: 'New Section 1 Title',
    section1_description: 'New content here...'
  })
});
```

### 2. Upload New Section Image
```javascript
const formData = new FormData();
formData.append('section1_image', newImageFile);

await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

### 3. Add New Subsection with Image
```javascript
// Step 1: Upload image separately (or use existing URL)
const imageUrl = 'https://res.cloudinary.com/.../new-subsection.jpg';

// Step 2: Add subsection
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    section3_subsections: [
      {
        title: 'New Subsection',
        description: 'Content here',
        image: imageUrl,
        sort_order: 4,
        is_active: true
      }
    ]
  })
});
```

### 4. Update Existing Subsection
```javascript
// Include the 'id' field to update
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    section3_subsections: [
      {
        id: 'uuid-of-existing-subsection',
        title: 'Updated Title',
        description: 'Updated content'
        // Image URL remains unchanged if not provided
      }
    ]
  })
});
```

### 5. Reorder Subsections
```javascript
// Update sort_order for multiple subsections
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    section3_subsections: [
      { id: 'uuid-1', sort_order: 2 },
      { id: 'uuid-2', sort_order: 1 },
      { id: 'uuid-3', sort_order: 3 }
    ]
  })
});
```

---

## Important Notes

1. **Subsection ID Behavior:**
   - With `id`: Updates existing subsection
   - Without `id`: Creates new subsection
   - Omitted subsections: NOT automatically deleted (must delete manually)

2. **Image Handling:**
   - Section 1 & 2: Binary upload via multipart OR URL via JSON
   - Subsections: URL reference only (upload images separately first)

3. **Partial Updates:**
   - PATCH allows updating only specific fields
   - Omitted fields retain their current values
   - Empty string `""` clears the field

4. **Singleton Pattern:**
   - Only one Our Story page exists (id=1)
   - Cannot create new pages, only update existing

5. **Image URLs:**
   - Accept full Cloudinary URLs
   - Accept public_id (Cloudinary asset name)
   - NULL or empty string removes image

---

## Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "message": "Validation error.",
  "errors": {
    "section3_subsections": [
      {
        "title": ["This field is required."]
      }
    ]
  }
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**404 Not Found:**
(Should not occur - page auto-created as singleton)

---

## Testing Examples

### cURL Examples

**Get Public Story:**
```bash
curl https://api.example.com/api/v1/our-story/
```

**Get Admin Story:**
```bash
curl https://api.example.com/api/v1/admin/our-story/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update with JSON:**
```bash
curl -X PATCH https://api.example.com/api/v1/admin/our-story/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Our Amazing Story",
    "section1_title": "The Beginning"
  }'
```

**Upload Image:**
```bash
curl -X PATCH https://api.example.com/api/v1/admin/our-story/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "section1_image=@image.jpg"
```
