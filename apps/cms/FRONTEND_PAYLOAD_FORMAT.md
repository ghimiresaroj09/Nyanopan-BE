# Frontend Payload Format - Our Story & Sustainability

## ✅ CONFIRMED: Your Format is Correct!

The backend now accepts **exactly the format** your frontend is sending.

---

## Our Story - Accepted Payload

### ✅ Your Format (CORRECT)
```json
{
  "title": "Our Story",
  "description": "<p>Our atelier is small by choice. Every slipper carries the stitched signature initials of the artisan who shaped it.</p>",
  
  "section1": {
    "title": "From fleece to sole",
    "description": "Every pair begins as raw Nepali wool, washed and felted by hand in our Kathmandu workshop.",
    "image": "https://res.cloudinary.com/xolsowjk/image/upload/v1/ecommerce/story/section1.jpg"
  },
  
  "section2": {
    "title": "The atelier",
    "description": "Small by choice — every craftsperson shapes a pair from start to finish.",
    "image": ""
  },
  
  "section3": {
    "title": "Our Journey",
    "subsections": [
      {
        "title": "2019 — First workshop",
        "description": "Started with two felters and one carding machine.",
        "image": "https://res.cloudinary.com/xolsowjk/image/upload/v1/ecommerce/story/journey-2019.jpg",
        "sort_order": 0,
        "is_active": true
      },
      {
        "title": "2024 — Going abroad",
        "description": "First export orders from Europe and Japan.",
        "image": "",
        "sort_order": 1,
        "is_active": true
      }
    ]
  }
}
```

### Key Points:
✅ **Nested structure** for sections (section1, section2, section3)  
✅ **Empty strings** for images are handled (converted to `null`)  
✅ **HTML content** in description fields is supported  
✅ **Subsections without `id`** = create new  
✅ **Subsections with `id`** = update existing  

---

## Our Sustainability - Accepted Payload

### ✅ Expected Format
```json
{
  "title": "Our Sustainability",
  "description": "<p>Our commitment to environmental and social responsibility.</p>",
  
  "sections": [
    {
      "title": "Eco-Friendly Materials",
      "description": "We use sustainable and organic materials in all our products.",
      "image": "https://res.cloudinary.com/xolsowjk/image/upload/v1/ecommerce/sustainability/materials.jpg",
      "sort_order": 0,
      "is_active": true
    },
    {
      "title": "Fair Trade Practices",
      "description": "We ensure fair wages and safe working conditions.",
      "image": "",
      "sort_order": 1,
      "is_active": true
    }
  ]
}
```

### Key Points:
✅ **Flat array** of sections (not nested in subsections)  
✅ **Empty strings** for images are handled  
✅ **HTML content** supported  
✅ **Sections without `id`** = create new  
✅ **Sections with `id`** = update existing  

---

## Image Handling

### Empty Image String
```json
"image": ""  // ✅ Accepted - will set to null/remove image
```

### Image URL
```json
"image": "https://res.cloudinary.com/xolsowjk/image/upload/v1/ecommerce/story/section1.jpg"
```

### No Image (New Items)
```json
"image": ""  // or omit the field entirely
```

---

## Creating vs Updating Subsections/Sections

### Create New Subsection (No ID)
```json
{
  "title": "2025 — Global expansion",
  "description": "Opening new markets in North America.",
  "image": "https://res.cloudinary.com/.../2025.jpg",
  "sort_order": 2,
  "is_active": true
}
```

### Update Existing Subsection (With ID)
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "2024 — Going abroad (Updated)",
  "description": "Updated description...",
  "image": "https://res.cloudinary.com/.../updated.jpg",
  "sort_order": 1,
  "is_active": true
}
```

### Important Notes:
- **Including `id`**: Updates the existing item with that ID
- **Omitting `id`**: Creates a new item
- **Omitting an existing item from the array**: Does NOT delete it (manual deletion required)

---

## Complete Examples

### Example 1: Update Story Title Only
```json
{
  "title": "Our Amazing Story"
}
```

### Example 2: Update Section 1 Content
```json
{
  "section1": {
    "title": "Updated Title",
    "description": "Updated description",
    "image": "https://res.cloudinary.com/.../new-image.jpg"
  }
}
```

### Example 3: Add New Subsection to Section 3
```json
{
  "section3": {
    "subsections": [
      {
        "id": "existing-uuid-1",
        "title": "Keep existing 1",
        "description": "...",
        "sort_order": 0,
        "is_active": true
      },
      {
        "id": "existing-uuid-2",
        "title": "Keep existing 2",
        "description": "...",
        "sort_order": 1,
        "is_active": true
      },
      {
        "title": "New subsection",
        "description": "Brand new content",
        "image": "https://res.cloudinary.com/.../new.jpg",
        "sort_order": 2,
        "is_active": true
      }
    ]
  }
}
```

### Example 4: Disable a Subsection
```json
{
  "section3": {
    "subsections": [
      {
        "id": "uuid-to-disable",
        "is_active": false
      }
    ]
  }
}
```

---

## Response Format

When you GET the data, you'll receive the same structure:

```json
{
  "success": true,
  "message": "Our Story page retrieved successfully.",
  "data": {
    "id": 1,
    "title": "Our Story",
    "description": "<p>Content here...</p>",
    "section1": {
      "title": "From fleece to sole",
      "description": "Content...",
      "image": "https://res.cloudinary.com/.../section1.jpg"
    },
    "section2": {
      "title": "The atelier",
      "description": "Content...",
      "image": "https://res.cloudinary.com/.../section2.jpg"
    },
    "section3": {
      "title": "Our Journey",
      "subsections": [
        {
          "id": "uuid-1",
          "title": "2019 — First workshop",
          "description": "Started with two felters...",
          "image": "https://res.cloudinary.com/.../journey-2019.jpg",
          "sort_order": 0,
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

## Frontend Implementation Example

### React Hook for Our Story
```typescript
import { useState, useEffect } from 'react';

interface StorySubsection {
  id?: string;
  title: string;
  description: string;
  image: string;
  sort_order: number;
  is_active: boolean;
}

interface StoryData {
  title: string;
  description: string;
  section1: {
    title: string;
    description: string;
    image: string;
  };
  section2: {
    title: string;
    description: string;
    image: string;
  };
  section3: {
    title: string;
    subsections: StorySubsection[];
  };
}

function useOurStory() {
  const [story, setStory] = useState<StoryData | null>(null);
  
  const fetchStory = async () => {
    const response = await fetch('/api/v1/admin/our-story/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setStory(data.data);
  };
  
  const updateStory = async (updates: Partial<StoryData>) => {
    const response = await fetch('/api/v1/admin/our-story/', {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    if (response.ok) {
      await fetchStory(); // Refresh data
    }
    
    return response;
  };
  
  const addSubsection = async (subsection: Omit<StorySubsection, 'id'>) => {
    if (!story) return;
    
    const updatedSubsections = [
      ...story.section3.subsections,
      subsection
    ];
    
    return updateStory({
      section3: {
        title: story.section3.title,
        subsections: updatedSubsections
      }
    });
  };
  
  const updateSubsection = async (id: string, updates: Partial<StorySubsection>) => {
    if (!story) return;
    
    const updatedSubsections = story.section3.subsections.map(sub =>
      sub.id === id ? { ...sub, ...updates } : sub
    );
    
    return updateStory({
      section3: {
        title: story.section3.title,
        subsections: updatedSubsections
      }
    });
  };
  
  useEffect(() => {
    fetchStory();
  }, []);
  
  return { story, updateStory, addSubsection, updateSubsection };
}
```

### Usage Example
```typescript
function StoryEditor() {
  const { story, updateStory, addSubsection } = useOurStory();
  
  const handleUpdateSection1 = async () => {
    await updateStory({
      section1: {
        title: "New Title",
        description: "New description",
        image: "https://res.cloudinary.com/.../new.jpg"
      }
    });
  };
  
  const handleAddSubsection = async () => {
    await addSubsection({
      title: "2025 — New Milestone",
      description: "Our latest achievement",
      image: "",
      sort_order: story!.section3.subsections.length,
      is_active: true
    });
  };
  
  // ... render UI
}
```

---

## Common Mistakes to Avoid

❌ **Don't use flat structure for sections:**
```json
{
  "section1_title": "Wrong",  // ❌ This won't work anymore
  "section1_description": "Wrong"
}
```

✅ **Use nested structure:**
```json
{
  "section1": {  // ✅ Correct
    "title": "Right",
    "description": "Right"
  }
}
```

❌ **Don't send `null` for image if you want to keep existing:**
```json
{
  "section1": {
    "title": "Update title only",
    "image": null  // ❌ This will remove the image
  }
}
```

✅ **Omit image field or send existing URL:**
```json
{
  "section1": {
    "title": "Update title only"
    // ✅ Omit image to keep existing
  }
}
```

---

## Summary

Your frontend payload format is **100% correct** and the backend now accepts it exactly as you're sending it:

✅ Nested sections (section1, section2, section3)  
✅ Empty strings for images (auto-converted to null)  
✅ HTML in descriptions  
✅ Subsections with/without IDs  
✅ sort_order and is_active fields  

No changes needed on the frontend! 🎉
