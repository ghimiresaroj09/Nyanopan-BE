# CMS Image Upload Guide

## Overview
All CMS image fields now support **binary file uploads** using `multipart/form-data`. Images are stored in Cloudinary and validated automatically.

## Affected Endpoints

### 1. Team Members
**Endpoint:** `POST/PUT/PATCH /api/v1/admin/team-members/`

**Fields with Image Upload:**
- `image` - Team member photo

### 2. Our Story
**Endpoint:** `PUT/PATCH /api/v1/admin/our-story/`

**Fields with Image Upload:**
- `section1_image` - Section 1 image
- `section2_image` - Section 2 image
- Nested subsections: `section3_subsections[].image`

### 3. Our Sustainability
**Endpoint:** `PUT/PATCH /api/v1/admin/our-sustainability/`

**Fields with Image Upload:**
- Nested sections: `sections[].image`

## Upload Methods

### Method 1: Direct Binary Upload (Simple Fields)

For single image uploads like team members:

```bash
curl -X POST http://localhost:8000/api/v1/admin/team-members/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=John Doe" \
  -F "role=Master Craftsman" \
  -F "intro=Expert artisan with 20 years experience" \
  -F "image=@/path/to/photo.jpg" \
  -F "sort_order=1" \
  -F "is_active=true"
  # our_makers field is optional - defaults to the singleton Our Makers page
```

**JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('name', 'John Doe');
formData.append('role', 'Master Craftsman');
formData.append('intro', 'Expert artisan...');
formData.append('image', fileInput.files[0]); // File from <input type="file">
formData.append('sort_order', '1');
formData.append('is_active', 'true');

const response = await fetch('/api/v1/admin/team-members/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

### Method 2: Our Story Page Updates

For Our Story main sections (section1, section2):

```bash
# Update story sections with images
curl -X PATCH http://localhost:8000/api/v1/admin/our-story/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Our Story" \
  -F "section1_title=The Beginning" \
  -F "section1_description=How we started..." \
  -F "section1_image=@/path/to/section1.jpg" \
  -F "section2_title=Our Growth" \
  -F "section2_description=How we expanded..." \
  -F "section2_image=@/path/to/section2.jpg"
```

**JavaScript:**
```javascript
const formData = new FormData();
formData.append('title', 'Our Story');
formData.append('section1_title', 'The Beginning');
formData.append('section1_description', 'How we started...');
formData.append('section1_image', section1File);  // File object
formData.append('section2_title', 'Our Growth');
formData.append('section2_image', section2File);

await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

### Method 3: Nested Subsections/Sections

**For Our Story subsections and Sustainability sections:**

Since these are nested arrays, there are two approaches:

#### Approach A: JSON with Image URLs (Recommended for Nested Updates)
1. First, upload images individually (if needed)
2. Then update page with URLs

```javascript
// Step 1: Upload new images if needed (optional helper endpoint)
const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);
  // You can create a dedicated image upload endpoint or use product image upload
  const response = await fetch('/api/v1/upload-image/', {
    method: 'POST',
    body: formData
  });
  const data = await response.json();
  return data.url;
};

// Step 2: Update page with nested data using URLs
const subsections = [
  {
    id: 1,  // existing subsection
    title: 'Updated',
    description: 'Updated content',
    image: 'https://cloudinary.com/existing.jpg',  // URL or public_id
    sort_order: 1,
    is_active: true
  },
  {
    // no id = new subsection
    title: 'New Subsection',
    description: 'New content',
    image: await uploadImage(newImageFile),  // Upload first, then use URL
    sort_order: 2,
    is_active: true
  }
];

await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Our Story',
    section3_title: 'Our Journey',
    section3_subsections: subsections
  })
});
```

#### Approach B: Multipart with Nested JSON (Advanced)
```javascript
// Combine files and JSON in one request
const formData = new FormData();

// Add text fields
formData.append('title', 'Our Story');
formData.append('section3_title', 'Our Journey');

// Add subsections as JSON (without image files)
const subsectionsData = [
  { id: 1, title: 'Updated', description: 'text', image: 'subsection_1_image' },
  { title: 'New', description: 'text', image: 'subsection_2_image' }
];
formData.append('section3_subsections', JSON.stringify(subsectionsData));

// Add actual image files with referenced names
formData.append('subsection_1_image', existingUrlOrFile1);
formData.append('subsection_2_image', file2);

// Note: This requires custom serializer logic to resolve file references
// Current implementation uses Approach A (JSON with URLs)
```

### Method 3: URL Reference (Existing Images)

If image already exists in Cloudinary, you can pass URL or public_id:

```javascript
const data = {
  name: 'John Doe',
  role: 'Designer',
  intro: 'Creative expert...',
  image: 'https://res.cloudinary.com/your-cloud/image/upload/v123/file.jpg',
  // OR just the public_id: 'ecommerce/cms/team-members/abc123.jpg'
};

await fetch('/api/v1/admin/team-members/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

## Image Validation

All uploads are automatically validated:
- **Max size:** 10MB
- **Allowed formats:** JPEG, PNG, GIF, WEBP
- **Minimum dimensions:** 100x100 pixels
- **Storage:** Cloudinary (or configured storage backend)

## Response Format

**Successful Upload Response:**
```json
{
  "success": true,
  "message": "Team member created successfully.",
  "data": {
    "id": "uuid-here",
    "name": "John Doe",
    "role": "Master Craftsman",
    "image": "https://res.cloudinary.com/your-cloud/image/upload/v123/ecommerce/cms/team-members/abc123.jpg",
    "intro": "Expert artisan...",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

## Best Practices

### 1. Single Image Upload
Use `multipart/form-data` for direct binary uploads:
```javascript
const formData = new FormData();
formData.append('image', file);
// ... other fields
```

### 2. Update Without Changing Image
Omit the image field or send existing URL:
```javascript
// Option 1: Omit image field
const data = { name: 'New Name', role: 'New Role' };

// Option 2: Send existing URL back
const data = { 
  name: 'New Name',
  image: existingData.image  // Keep existing image
};
```

### 3. Clear/Remove Image
Send `null` or empty string:
```javascript
const data = {
  name: 'John Doe',
  image: null  // Removes image
};
```

### 4. Nested Updates with Images
For complex nested structures (Our Story subsections, Sustainability sections):
- **Recommended:** Use JSON payload with image URLs
  - First upload images separately (or use existing Cloudinary URLs)
  - Then send nested JSON with URL references
- **Alternative:** For simple updates without image changes, use JSON with existing URLs

**Example workflow:**
```javascript
// 1. Upload new images first (if needed)
const newImageUrl = await uploadToCloudinary(file);

// 2. Update page with nested data including URLs
await fetch('/api/v1/admin/our-story/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    section3_subsections: [
      { id: 1, title: 'Updated', image: existingUrl },  // Update existing
      { title: 'New', image: newImageUrl }  // Create new with uploaded image
    ]
  })
});
```

## Migration from URL-based to Binary Upload

If you have existing URL strings in the database:
1. ✅ **They will continue to work** - Django ImageField supports URL strings
2. New uploads will be stored as Cloudinary references
3. Gradual migration possible - mix both approaches

## Frontend Example (React)

```jsx
function TeamMemberForm() {
  const [imageFile, setImageFile] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('role', role);
    formData.append('intro', intro);
    
    if (imageFile) {
      formData.append('image', imageFile);
    }
    
    const response = await fetch('/api/v1/admin/team-members/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // NO Content-Type header - let browser set it with boundary
      },
      body: formData
    });
    
    const result = await response.json();
    console.log('Uploaded:', result.data.image);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => setImageFile(e.target.files[0])}
      />
      {/* other fields */}
      <button type="submit">Create Member</button>
    </form>
  );
}
```

## Troubleshooting

### Error: "Upload a valid image"
- Check file format (must be JPEG, PNG, GIF, or WEBP)
- Check file size (must be under 10MB)
- Check image dimensions (minimum 100x100px)

### Error: "Invalid image value"
- Ensure you're using `multipart/form-data` for binary uploads
- Check that field name matches API field name exactly

### Images not showing
- Verify Cloudinary configuration in `.env`
- Check that `CLOUDINARY_URL` is set correctly
- Verify image URL in response is accessible

## API Support Summary

| Endpoint | Binary Upload | URL Reference | Nested with Images |
|----------|--------------|---------------|-------------------|
| Team Members | ✅ Direct | ✅ | N/A |
| Our Story (section 1 & 2) | ✅ Direct | ✅ | N/A |
| Our Story (subsections) | ⚠️ See Method 3 | ✅ | Via JSON payload |
| Sustainability (sections) | ⚠️ See Method 3 | ✅ | Via JSON payload |

✅ = Fully supported
⚠️ = Use JSON with URLs approach for nested arrays with images
