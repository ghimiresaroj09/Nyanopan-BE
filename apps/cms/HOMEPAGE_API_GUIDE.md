# Homepage APIs - Complete Guide

## Overview
Two new homepage APIs have been created:
1. **Homepage Content** - Main homepage sections (3 sections)
2. **Homepage Collections** - Collections showcase with items

Both APIs follow the same pattern as other CMS APIs (Our Story, Sustainability).

---

## API 1: Homepage Content

### Endpoints
```
GET    /api/v1/homepage/              (Public - no auth)
GET    /api/v1/admin/homepage/        (Admin - requires auth)
PUT    /api/v1/admin/homepage/        (Admin - full update)
PATCH  /api/v1/admin/homepage/        (Admin - partial update)
```

### Response Structure (GET)

```json
{
  "success": true,
  "message": "Homepage content retrieved successfully.",
  "data": {
    "id": 1,
    "section1": {
      "tag": "Handcrafted Excellence",
      "image": "https://res.cloudinary.com/.../hero.jpg",
      "title": "Authentic Nepali Slippers",
      "description": "Each pair handmade by master artisans",
      "quote": "Comfort meets tradition"
    },
    "section2": {
      "tag": "Why Choose Us",
      "title": "Our Difference",
      "description": "What makes our slippers special",
      "image": "https://res.cloudinary.com/.../features.jpg",
      "feature": [
        {
          "title": "100% Natural Wool",
          "intro": "Sourced from Himalayan sheep"
        },
        {
          "title": "Fair Trade Certified",
          "intro": "Supporting local communities"
        }
      ]
    },
    "section3": {
      "tag": "About Us",
      "title": "Our Story",
      "image": "https://res.cloudinary.com/.../workshop.jpg",
      "description": "Founded in 2019 in Kathmandu..."
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Update Payload (PATCH/PUT)

```json
{
  "section1": {
    "tag": "Handcrafted Excellence",
    "image": "https://res.cloudinary.com/.../hero.jpg",
    "title": "Authentic Nepali Slippers",
    "description": "Each pair handmade by master artisans",
    "quote": "Comfort meets tradition"
  },
  "section2": {
    "tag": "Why Choose Us",
    "title": "Our Difference",
    "description": "What makes our slippers special",
    "image": "https://res.cloudinary.com/.../features.jpg",
    "feature": [
      {
        "title": "100% Natural Wool",
        "intro": "Sourced from Himalayan sheep"
      },
      {
        "title": "Fair Trade Certified",
        "intro": "Supporting local communities"
      }
    ]
  },
  "section3": {
    "tag": "About Us",
    "title": "Our Story",
    "image": "https://res.cloudinary.com/.../workshop.jpg",
    "description": "Founded in 2019 in Kathmandu..."
  }
}
```

### Field Reference

#### Section 1
| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Section tag/label |
| `image` | url | Hero image URL |
| `title` | string | Main title |
| `description` | text | Description |
| `quote` | text | Quote/tagline |

#### Section 2
| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Section tag/label |
| `title` | string | Section title |
| `description` | text | Section description |
| `image` | url | Section image URL |
| `feature` | array | Array of feature objects |

**Feature Object:**
| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Feature title |
| `intro` | string | Feature introduction |

#### Section 3
| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Section tag/label |
| `title` | string | Section title |
| `image` | url | Section image URL |
| `description` | text | Section description |

---

## API 2: Homepage Collections

### Endpoints
```
GET    /api/v1/homepage/collections/              (Public - no auth)
GET    /api/v1/admin/homepage/collections/        (Admin - requires auth)
PUT    /api/v1/admin/homepage/collections/        (Admin - full update)
PATCH  /api/v1/admin/homepage/collections/        (Admin - partial update)
```

### Response Structure (GET)

```json
{
  "success": true,
  "message": "Homepage collections retrieved successfully.",
  "data": {
    "id": 1,
    "tag": "Collections",
    "title": "Explore Our Collections",
    "description": "Discover our range of handcrafted slippers",
    "collections": [
      {
        "id": "uuid-1",
        "image": "https://res.cloudinary.com/.../indoor.jpg",
        "name": "Indoor Comfort",
        "intro": "Perfect for cozy nights at home",
        "link": "/indoor",
        "sort_order": 1,
        "is_active": true
      },
      {
        "id": "uuid-2",
        "image": "https://res.cloudinary.com/.../outdoor.jpg",
        "name": "Outdoor Adventure",
        "intro": "Durable slippers for outdoor use",
        "link": "/outdoor",
        "sort_order": 2,
        "is_active": true
      }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Public Response (No IDs, only active items)
```json
{
  "success": true,
  "data": {
    "tag": "Collections",
    "title": "Explore Our Collections",
    "description": "Discover our range of handcrafted slippers",
    "collections": [
      {
        "image": "https://res.cloudinary.com/.../indoor.jpg",
        "name": "Indoor Comfort",
        "intro": "Perfect for cozy nights at home",
        "link": "/indoor"
      }
    ]
  }
}
```

### Update Payload (PATCH/PUT)

**Without IDs (Replace All):**
```json
{
  "tag": "Collections",
  "title": "Explore Our Collections",
  "description": "Discover our range",
  "collections": [
    {
      "image": "https://res.cloudinary.com/.../indoor.jpg",
      "name": "Indoor Comfort",
      "intro": "Perfect for cozy nights at home",
      "link": "/indoor",
      "sort_order": 1,
      "is_active": true
    },
    {
      "image": "https://res.cloudinary.com/.../outdoor.jpg",
      "name": "Outdoor Adventure",
      "intro": "Durable slippers for outdoor use",
      "link": "/outdoor",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

**With IDs (Update Existing):**
```json
{
  "collections": [
    {
      "id": "existing-uuid-1",
      "name": "Updated Name",
      "intro": "Updated intro"
    },
    {
      "image": "",
      "name": "New Collection",
      "intro": "Brand new item",
      "link": "/new",
      "sort_order": 3,
      "is_active": true
    }
  ]
}
```

### Field Reference

#### Collections Page
| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Section tag/label |
| `title` | string | Collections section title |
| `description` | text | Collections description |
| `collections` | array | Array of collection items |

#### Collection Item
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | uuid | conditional | Include for update, omit for create |
| `image` | url | optional | Collection image URL |
| `name` | string | required | Collection name |
| `intro` | text | required | Collection introduction |
| `link` | string | required | Internal link path (e.g., `/indoor`) |
| `sort_order` | integer | optional | Display order (default: 0) |
| `is_active` | boolean | optional | Visibility (default: true) |

---

## Link Field Format

The `link` field stores internal route paths that your frontend will handle:

**Examples:**
- `/indoor` → Frontend routes to indoor collection page
- `/outdoor` → Frontend routes to outdoor collection page  
- `/inside` → Frontend routes to inside collection page
- `/slippers/wool` → Frontend routes to wool slippers page

**Notes:**
- Just store the path as a string (e.g., `"/indoor"`)
- No full URLs needed
- Your frontend router handles the navigation
- Admin enters the path, frontend handles routing logic

---

## Frontend Usage Examples

### 1. Fetch Homepage Content
```javascript
const response = await fetch('/api/v1/homepage/');
const data = await response.json();

// Use in components
<Hero
  tag={data.data.section1.tag}
  title={data.data.section1.title}
  image={data.data.section1.image}
  description={data.data.section1.description}
  quote={data.data.section1.quote}
/>

<Features
  title={data.data.section2.title}
  features={data.data.section2.feature}
/>
```

### 2. Fetch Collections
```javascript
const response = await fetch('/api/v1/homepage/collections/');
const data = await response.json();

// Render collections
{data.data.collections.map(collection => (
  <CollectionCard
    key={collection.name}
    image={collection.image}
    name={collection.name}
    intro={collection.intro}
    onClick={() => navigate(collection.link)}  // Use link for routing
  />
))}
```

### 3. Update Homepage (Admin)
```javascript
await fetch('/api/v1/admin/homepage/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    section1: {
      title: "Updated Title",
      image: "https://res.cloudinary.com/.../new.jpg"
    }
  })
});
```

### 4. Replace All Collections (Admin)
```javascript
// No IDs = replace all
await fetch('/api/v1/admin/homepage/collections/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    collections: [
      {
        name: "New Collection 1",
        intro: "Description",
        link: "/collection-1",
        image: "https://res.cloudinary.com/.../img1.jpg",
        sort_order: 0,
        is_active: true
      },
      {
        name: "New Collection 2",
        intro: "Description",
        link: "/collection-2",
        image: "",
        sort_order: 1,
        is_active: true
      }
    ]
  })
});
```

---

## Key Features

✅ **Singleton Pattern** - Only one Homepage and one Collections page exists  
✅ **Nested Updates** - All sections/collections updated in single request  
✅ **Replace Mode** - Send collections without IDs to replace all  
✅ **Update Mode** - Send collections with IDs to update specific items  
✅ **Empty Strings** - Accepted for images (stored as empty string)  
✅ **URL Storage** - Images stored as Cloudinary URLs (not binary)  
✅ **Public/Admin** - Separate endpoints for public (no auth) and admin  
✅ **Active Filtering** - Public API only shows `is_active=true` items  

---

## Important Notes

1. **Image URLs**: Upload images separately, use returned URLs in payloads
2. **Link Format**: Just the path string (e.g., `"/indoor"`), not full URL
3. **Features Array**: Stored as JSON in database (section2.feature)
4. **Collections Ordering**: Use `sort_order` field (lower = first)
5. **Replace vs Update**: No IDs = replace all, With IDs = update by ID
6. **Singleton Pages**: Cannot create multiple, only update existing (id=1)

---

## Summary

### Homepage Content API
- 3 sections with different structures
- Section 1: Hero with quote
- Section 2: Features array
- Section 3: About section
- All fields optional for updates

### Collections API
- Main page with tag, title, description
- Nested collections array
- Each collection has image, name, intro, link
- Link is internal path for frontend routing
- Replace or update modes supported

Both APIs ready for integration! 🎉
