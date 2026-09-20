# Product Filter Update - Summary

## What Changed

Added two new filtering capabilities to the public product list API (`GET /api/v1/products/`):

1. **Filter by Product Model**
2. **Filter by Attribute Values** (color, size, material, etc.)

---

## Files Modified

### 1. `apps/catalog/filters.py`

**Added:**
- `model` filter - Filter by product model slug
- `attribute` filter - Filter by attribute values with advanced logic

**New Features:**
```python
class ProductFilter(django_filters.FilterSet):
    # NEW: Filter by model slug
    model = django_filters.CharFilter(
        field_name="model__slug",
        lookup_expr="iexact"
    )
    
    # NEW: Filter by attribute values
    attribute = django_filters.CharFilter(
        method="filter_by_attribute"
    )
```

**Attribute Filter Logic:**
- Format: `attribute_slug:value_slug`
- Same attribute = OR logic: `?attribute=color:grey&attribute=color:black`
- Different attributes = AND logic: `?attribute=color:grey&attribute=size:large`

### 2. `apps/catalog/views/public.py`

**Updated:**
- API documentation to include new filter parameters
- Added examples for model and attribute filtering

---

## API Usage

### Filter by Model

```bash
# Get all products from "Celsi Wool Felt" model
GET /api/v1/products/?model=celsi-wool-felt
```

### Filter by Single Attribute

```bash
# Get all grey products
GET /api/v1/products/?attribute=color:grey
```

### Filter by Multiple Values (OR)

```bash
# Get products that are grey OR black
GET /api/v1/products/?attribute=color:grey&attribute=color:black
```

### Filter by Multiple Attributes (AND)

```bash
# Get products that are grey AND large
GET /api/v1/products/?attribute=color:grey&attribute=size:large
```

### Combined Filters

```bash
# Women's products from specific model with grey color
GET /api/v1/products/?model=celsi-wool-felt&gender=WOMEN&attribute=color:grey&ordering=price_asc
```

---

## Complete Filter Reference

| Filter | Example | Description |
|--------|---------|-------------|
| `category` | `?category=indoor-slippers` | Filter by category slug |
| `model` | `?model=celsi-wool-felt` | **NEW:** Filter by model slug |
| `gender` | `?gender=WOMEN` | Filter by gender |
| `usage_location` | `?usage_location=INSIDE` | Filter by usage location |
| `sole_type` | `?sole_type=RUBBER` | Filter by sole type |
| `is_featured` | `?is_featured=true` | Featured products only |
| `min_price` | `?min_price=1000` | Minimum price filter |
| `max_price` | `?max_price=5000` | Maximum price filter |
| `attribute` | `?attribute=color:grey` | **NEW:** Filter by attribute value |
| `search` | `?search=wool` | Full text search |
| `ordering` | `?ordering=price_asc` | Sort results |

---

## Frontend Integration Example

```javascript
// Build filter URL
const buildFilterUrl = (filters) => {
  const params = new URLSearchParams();
  
  // Model filter
  if (filters.model) {
    params.append('model', filters.model);
  }
  
  // Attribute filters (multiple allowed)
  filters.attributes?.forEach(attr => {
    params.append('attribute', `${attr.slug}:${attr.value}`);
  });
  
  // Other filters
  if (filters.category) params.append('category', filters.category);
  if (filters.gender) params.append('gender', filters.gender);
  if (filters.ordering) params.append('ordering', filters.ordering);
  
  return `/api/v1/products/?${params.toString()}`;
};

// Example usage
const url = buildFilterUrl({
  model: 'celsi-wool-felt',
  gender: 'WOMEN',
  attributes: [
    { slug: 'color', value: 'grey' },
    { slug: 'color', value: 'black' },
    { slug: 'size', value: 'large' }
  ],
  ordering: 'price_asc'
});

// Result: /api/v1/products/?model=celsi-wool-felt&attribute=color:grey&attribute=color:black&attribute=size:large&gender=WOMEN&ordering=price_asc
```

---

## Testing

### Test Endpoints

```bash
# 1. Filter by model
curl "https://nyanopan.onrender.com/api/v1/products/?model=celsi-wool-felt"

# 2. Filter by attribute (single)
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey"

# 3. Filter by multiple attributes (OR)
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey&attribute=color:black"

# 4. Filter by multiple attributes (AND)
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey&attribute=size:large"

# 5. Combined filters
curl "https://nyanopan.onrender.com/api/v1/products/?model=celsi-wool-felt&attribute=color:grey&gender=WOMEN&ordering=price_asc"
```

### Expected Response Format

```json
{
  "success": true,
  "message": "Products retrieved successfully.",
  "data": [
    {
      "id": "uuid",
      "name": "Product Name",
      "slug": "product-slug",
      "gender": "WOMEN",
      "category": {
        "id": "uuid",
        "name": "Category Name",
        "slug": "category-slug"
      },
      "model": {
        "id": "uuid",
        "name": "Model Name",
        "slug": "model-slug"
      },
      "is_featured": true,
      "price_range": {
        "min_price": "3,500.00",
        "max_price": "4,200.00"
      },
      "primary_image": {
        "url": "https://...",
        "title": "...",
        "alt": "..."
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Use Cases

### 1. Model Collection Page
Show all products from a specific collection/model:
```
GET /api/v1/products/?model=celsi-wool-felt&ordering=newest
```

### 2. Color Filter
Let users filter by color:
```
GET /api/v1/products/?attribute=color:grey&attribute=color:black
```

### 3. Size and Color Filter
Filter by multiple attributes:
```
GET /api/v1/products/?attribute=color:grey&attribute=size:large
```

### 4. Advanced Product Page
Combine all filters:
```
GET /api/v1/products/?category=indoor-slippers&model=celsi-wool-felt&gender=WOMEN&attribute=color:grey&sole_type=RUBBER&min_price=2000&max_price=6000&ordering=price_asc
```

---

## Performance

- Uses database indexes for efficient filtering
- `.distinct()` applied to avoid duplicate results
- Only active records (`is_active=True`) are returned
- Compatible with pagination

---

## Summary

✅ **Model filtering** - Filter by product model slug  
✅ **Attribute filtering** - Filter by any attribute value  
✅ **OR logic** - Multiple values for same attribute  
✅ **AND logic** - Multiple different attributes  
✅ **Backward compatible** - All existing filters still work  
✅ **Documented** - Full API documentation updated  
✅ **Production ready** - No breaking changes  

The public product API now supports comprehensive filtering for modern e-commerce filtering UIs! 🎉
