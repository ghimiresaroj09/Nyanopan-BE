# Our Sustainability API Payload Guide

## Endpoint
```
GET    /api/v1/our-sustainability/              (Public - no auth)
GET    /api/v1/admin/our-sustainability/        (Admin - requires auth)
PUT    /api/v1/admin/our-sustainability/        (Admin - full update)
PATCH  /api/v1/admin/our-sustainability/        (Admin - partial update)
```

---

## Response Structure (GET)

### Public Response
```json
{
  "success": true,
  "message": "Our Sustainability page retrieved successfully.",
  "data": {
    "title": "Our Sustainability",
    "description": "Our commitment to environmental and social responsibility",
    "sections": [
      {
        "title": "Eco-Friendly Materials",
        "description": "We use sustainable and organic materials...",
        "image": "https://res.cloudinary.com/.../eco-materials.jpg"
      },
      {
        "title": "Fair Trade Practices",
        "description": "We ensure fair wages and working conditions...",
        "image": "https://res.cloudinary.com/.../fair-trade.jpg"
      },
      {
        "title": "Carbon Neutral Shipping",
        "description": "All our shipments offset their carbon footprint...",
        "image": "https://res.cloudinary.com/.../carbon-neutral.jpg"
      }
    ]
  }
}
```

### Admin Response
```json
{
  "success": true,
  "message": "Our Sustainability page retrieved successfully.",
  "data": {
    "id": 1,
    "title": "Our Sustainability",
    "description": "Our commitment to environmental and social responsibility",
    "sections": [
      {
        "id": "uuid-1",
        "title": "Eco-Friendly Materials",
        "description": "We use sustainable and organic materials...",
        "image": "https://res.cloudinary.com/.../eco-materials.jpg",
        "sort_order": 1,
        "is_active": true
      },
      {
        "id": "uuid-2",
        "title": "Fair Trade Practices",
        "description": "We ensure fair wages and working conditions...",
        "image": "https://res.cloudinary.com/.../fair-trade.jpg",
        "sort_order": 2,
        "is_active": true
      },
      {
        "id": "uuid-3",
        "title": "Carbon Neutral Shipping",
        "description": "All our shipments offset their carbon footprint...",
        "image": "https://res.cloudinary.com/.../carbon-neutral.jpg",
        "sort_order": 3,
        "is_active": true
      }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Update Payloads (PUT/PATCH)

### Method 1: JSON Payload (Recommended)

Use this for updating content and sections with existing image URLs.

#### Update Main Content Only
```json
{
  "title": "Our Sustainability Commitment",
  "description": "Updated main description about our sustainability efforts"
}
```

#### Update Existing Section
```json
{
  "sections": [
    {
      "id": "uuid-1",
      "title": "Updated Section Title",
      "description": "Updated section content",
      "image": "https://res.cloudinary.com/.../updated-image.jpg",
      "sort_order": 1,
      "is_active": true
    }
  ]
}
```

#### Create New Section
```json
{
  "sections": [
    {
      "title": "New Sustainability Initiative",
      "description": "Our latest environmental program...",
      "image": "https://res.cloudinary.com/.../new-initiative.jpg",
      "sort_order": 4,
      "is_active": true
    }
  ]
}
```

#### Mix Update & Create
```json
{
  "sections": [
    {
      "id": "uuid-1",
      "title": "Updated Eco Materials",
      "description": "Updated content",
      "image": "https://res.cloudinary.com/.../eco.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "id": "uuid-2",
      "title": "Updated Fair Trade",
      "description": "Updated content",
      "sort_order": 2,
      "is_active": false
    },
    {
      "title": "New Zero Waste Program",
      "description": "Our new waste reduction initiative",
      "image": "https://res.cloudinary.com/.../zero-waste.jpg",
      "sort_order": 3,
      "is_active": true
    }
  ]
}
```

#### Full Page Update
```json
{
  "title": "Our Sustainability",
  "description": "Complete description of our commitment",
  "sections": [
    {
      "id": "uuid-1",
      "title": "Eco-Friendly Materials",
      "description": "Full description...",
      "image": "https://res.cloudinary.com/.../materials.jpg",
      "sort_order": 1,
      "is_active": true
    },
    {
      "title": "New Section",
      "description": "Brand new content...",
      "image": "https://res.cloudinary.com/.../new.jpg",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

---

### Method 2: Multipart/Form-Data (Not Recommended for Nested Arrays)

Multipart is supported for the endpoint, but since sections are nested arrays, it's complex. Use JSON with image URLs instead.

If you need to upload images:
1. Upload images separately (to product image upload or dedicated endpoint)
2. Use the returned URLs in JSON payload

---

## Field Reference

### Root Level Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | read-only | Always 1 (singleton) |
| `title` | string | optional | Main page title (default: "Our Sustainability") |
| `description` | text | optional | Main introduction text |
| `sections` | array | optional | Array of section objects |
| `created_at` | datetime | read-only | Creation timestamp |
| `updated_at` | datetime | read-only | Last update timestamp |

### Section Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | uuid | conditional | Required for update, omit for create |
| `title` | string | required | Section title |
| `description` | text | required | Section content |
| `image` | url | optional | Image URL (Cloudinary) |
| `sort_order` | integer | optional | Display order (default: 0) |
| `is_active` | boolean | optional | Visibility status (default: true) |

---

## Common Workflows

### 1. Update Only Text (No Images)
```javascript
await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Updated Sustainability Title',
    description: 'Updated main description'
  })
});
```

### 2. Add New Section with Image
```javascript
// Use existing image URL or upload separately first
const imageUrl = 'https://res.cloudinary.com/.../new-section.jpg';

await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sections: [
      {
        title: 'New Initiative',
        description: 'Our latest sustainability program...',
        image: imageUrl,
        sort_order: 5,
        is_active: true
      }
    ]
  })
});
```

### 3. Update Existing Section
```javascript
await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sections: [
      {
        id: 'uuid-of-existing-section',
        title: 'Updated Title',
        description: 'Updated content',
        // Image remains unchanged if not provided
        sort_order: 1,
        is_active: true
      }
    ]
  })
});
```

### 4. Disable Section (Hide from Public)
```javascript
await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sections: [
      {
        id: 'uuid-1',
        is_active: false  // Hide this section
      }
    ]
  })
});
```

### 5. Reorder Sections
```javascript
await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sections: [
      { id: 'uuid-1', sort_order: 3 },
      { id: 'uuid-2', sort_order: 1 },
      { id: 'uuid-3', sort_order: 2 }
    ]
  })
});
```

### 6. Update All Sections at Once
```javascript
// Get current data first
const currentData = await fetch('/api/v1/admin/our-sustainability/').then(r => r.json());

// Modify as needed
const updatedSections = currentData.data.sections.map(section => ({
  id: section.id,
  title: section.title,
  description: section.description,
  image: section.image,
  sort_order: section.sort_order,
  is_active: section.is_active
}));

// Add new section
updatedSections.push({
  title: 'New Section',
  description: 'New content',
  image: 'https://res.cloudinary.com/.../new.jpg',
  sort_order: updatedSections.length + 1,
  is_active: true
});

// Send update
await fetch('/api/v1/admin/our-sustainability/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ sections: updatedSections })
});
```

---

## Important Notes

1. **Section ID Behavior:**
   - With `id`: Updates existing section
   - Without `id`: Creates new section
   - Omitted sections: NOT automatically deleted (must delete manually)

2. **Image Handling:**
   - Sections accept URL references only
   - Upload images separately, then use URL in payload
   - NULL or empty string removes image

3. **Partial Updates:**
   - PATCH allows updating only specific fields
   - Omitted fields retain their current values
   - Empty string `""` clears the field

4. **Singleton Pattern:**
   - Only one Sustainability page exists (id=1)
   - Cannot create new pages, only update existing

5. **Public Visibility:**
   - Only sections with `is_active=true` appear in public API
   - Disabled sections still exist in admin API

---

## Complete Frontend Example (React)

```jsx
import { useState, useEffect } from 'react';

function SustainabilityEditor() {
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPage();
  }, []);

  const fetchPage = async () => {
    const response = await fetch('/api/v1/admin/our-sustainability/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setPage(data.data);
    setLoading(false);
  };

  const updateSection = async (sectionIndex, updates) => {
    const updatedSections = [...page.sections];
    updatedSections[sectionIndex] = {
      ...updatedSections[sectionIndex],
      ...updates
    };

    const response = await fetch('/api/v1/admin/our-sustainability/', {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sections: updatedSections
      })
    });

    if (response.ok) {
      await fetchPage(); // Refresh
    }
  };

  const addSection = async (newSection) => {
    const response = await fetch('/api/v1/admin/our-sustainability/', {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sections: [
          ...page.sections,
          {
            title: newSection.title,
            description: newSection.description,
            image: newSection.imageUrl,
            sort_order: page.sections.length + 1,
            is_active: true
          }
        ]
      })
    });

    if (response.ok) {
      await fetchPage();
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>{page.title}</h1>
      <p>{page.description}</p>
      
      {page.sections.map((section, index) => (
        <div key={section.id}>
          <h2>{section.title}</h2>
          <p>{section.description}</p>
          <img src={section.image} alt={section.title} />
          <button onClick={() => updateSection(index, {
            is_active: !section.is_active
          })}>
            {section.is_active ? 'Disable' : 'Enable'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "message": "Validation error.",
  "errors": {
    "sections": [
      {
        "title": ["This field is required."],
        "description": ["This field is required."]
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

---

## Testing Examples

### cURL Examples

**Get Public Page:**
```bash
curl https://api.example.com/api/v1/our-sustainability/
```

**Get Admin Page:**
```bash
curl https://api.example.com/api/v1/admin/our-sustainability/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update Title:**
```bash
curl -X PATCH https://api.example.com/api/v1/admin/our-sustainability/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Our Green Commitment"
  }'
```

**Add New Section:**
```bash
curl -X PATCH https://api.example.com/api/v1/admin/our-sustainability/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sections": [
      {
        "title": "Renewable Energy",
        "description": "We power our facilities with 100% renewable energy",
        "image": "https://res.cloudinary.com/.../renewable.jpg",
        "sort_order": 4,
        "is_active": true
      }
    ]
  }'
```
