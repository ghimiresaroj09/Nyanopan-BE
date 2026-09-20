# Product Filtering Guide

## Overview

The public product list API (`GET /api/v1/products/`) now supports comprehensive filtering by:
- **Model** (product model slug)
- **Attribute Values** (color, size, material, etc.) - **Uses attribute NAMES, not slugs**
- **Category, Gender, Usage Location, Sole Type**
- **Price Range**
- **Featured Status**

---

## New Filtering Options

### 1. Filter by Product Model

Filter products by their product model slug.

**Parameter:** `model`

**Examples:**
```bash
# Get all products from "Celsi Wool Felt" model
GET /api/v1/products/?model=celsi-wool-felt

# Combine with other filters
GET /api/v1/products/?model=celsi-wool-felt&gender=WOMEN
```

**Use Case:**
- Show all products from a specific collection/model
- Model-specific landing pages
- "More from this collection" sections

---

### 2. Filter by Attribute Values

Filter products by their attribute values (color, size, material, etc.)

**Parameter:** `attribute`

**Format:** `attribute_name:value_name` (case-insensitive)

**⚠️ Important:** Use attribute **NAMES** (e.g., "Color", "Size"), NOT slugs. The Attribute and AttributeValue models don't have slug fields.

#### Single Attribute Value

```bash
# Get all grey products
GET /api/v1/products/?attribute=color:grey
GET /api/v1/products/?attribute=Color:Grey  # Case-insensitive

# Get all large products
GET /api/v1/products/?attribute=size:large
GET /api/v1/products/?attribute=Size:Large  # Also works
```

#### Multiple Attributes (AND Logic)

When you specify different attributes, products must match **ALL** specified attributes.

```bash
# Get products that are grey AND large
GET /api/v1/products/?attribute=color:grey&attribute=size:large

# Get products that are wool AND grey AND large
GET /api/v1/products/?attribute=material:wool&attribute=color:grey&attribute=size:large
```

**Result:** Products with color = grey **AND** size = large

---

## Complete Filtering Reference

### All Available Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `category` | String | Category slug | `?category=indoor-slippers` |
| `model` | String | Product model slug | `?model=celsi-wool-felt` |
| `gender` | Choice | `MEN`, `WOMEN`, `UNISEX`, `KIDS`, `BABY` | `?gender=WOMEN` |
| `usage_location` | Choice | `INSIDE`, `OUTSIDE`, `BOTH` | `?usage_location=INSIDE` |
| `sole_type` | Choice | `LEATHER`, `RUBBER` | `?sole_type=RUBBER` |
| `is_featured` | Boolean | `true`, `false` | `?is_featured=true` |
| `min_price` | Number | Minimum price (NPR) | `?min_price=1000` |
| `max_price` | Number | Maximum price (NPR) | `?max_price=5000` |
| `attribute` | String | `attribute_slug:value_slug` | `?attribute=color:grey` |
| `search` | String | Search name, description, model, category | `?search=wool` |
| `ordering` | String | Sort order (see below) | `?ordering=price_asc` |

---

## Sorting Options

### Available Sort Orders

| Parameter Value | Description | Technical |
|----------------|-------------|-----------|
| `price_asc` or `price` | Low to High | By minimum variant price |
| `price_desc` or `-price` | High to Low | By maximum variant price |
| `name_asc` or `name` | A to Z | Alphabetical ascending |
| `name_desc` or `-name` | Z to A | Alphabetical descending |
| `newest` or `-created_at` | Recently Added | Default sort |
| `oldest` or `created_at` | Previously Added | Oldest first |

**Examples:**
```bash
GET /api/v1/products/?ordering=price_asc
GET /api/v1/products/?ordering=name_desc
GET /api/v1/products/?ordering=newest
```

---

## Real-World Examples

### Example 1: Product Listing Page with Filters

```bash
# Women's indoor slippers, grey or black, sorted by price
GET /api/v1/products/?gender=WOMEN&usage_location=INSIDE&attribute=color:grey&attribute=color:black&ordering=price_asc
```

### Example 2: Model Collection Page

```bash
# All products from "Celsi Wool Felt" model, featured first
GET /api/v1/products/?model=celsi-wool-felt&ordering=newest
```

### Example 3: Category Page with Price Range

```bash
# Indoor slippers under 5000 NPR
GET /api/v1/products/?category=indoor-slippers&max_price=5000&ordering=price_asc
```

### Example 4: Advanced Multi-Attribute Filter

```bash
# Wool slippers that are (grey OR charcoal) with rubber sole
GET /api/v1/products/?attribute=material:wool&attribute=color:grey&attribute=color:charcoal&sole_type=RUBBER&ordering=price_asc
```

### Example 5: Search with Filters

```bash
# Search for "felt" in women's products
GET /api/v1/products/?search=felt&gender=WOMEN&ordering=name_asc
```

---

## Frontend Integration

### React/Next.js Filter Component

```jsx
import { useState, useEffect } from 'react';

export function ProductFilters({ onFilterChange }) {
  const [filters, setFilters] = useState({
    category: '',
    model: '',
    gender: '',
    usage_location: '',
    sole_type: '',
    is_featured: false,
    min_price: '',
    max_price: '',
    attributes: [], // Array of {slug, value} objects
    search: '',
    ordering: 'newest'
  });

  // Build query string
  const buildQueryString = () => {
    const params = new URLSearchParams();
    
    // Simple filters
    if (filters.category) params.append('category', filters.category);
    if (filters.model) params.append('model', filters.model);
    if (filters.gender) params.append('gender', filters.gender);
    if (filters.usage_location) params.append('usage_location', filters.usage_location);
    if (filters.sole_type) params.append('sole_type', filters.sole_type);
    if (filters.is_featured) params.append('is_featured', 'true');
    if (filters.min_price) params.append('min_price', filters.min_price);
    if (filters.max_price) params.append('max_price', filters.max_price);
    if (filters.search) params.append('search', filters.search);
    if (filters.ordering) params.append('ordering', filters.ordering);
    
    // Attribute filters - can have multiple
    filters.attributes.forEach(attr => {
      params.append('attribute', `${attr.slug}:${attr.value}`);
    });
    
    return params.toString();
  };

  // Fetch products when filters change
  useEffect(() => {
    const query = buildQueryString();
    onFilterChange(query);
  }, [filters]);

  // Add attribute filter
  const addAttributeFilter = (attributeSlug, valueSlug) => {
    setFilters(prev => ({
      ...prev,
      attributes: [...prev.attributes, { slug: attributeSlug, value: valueSlug }]
    }));
  };

  // Remove attribute filter
  const removeAttributeFilter = (attributeSlug, valueSlug) => {
    setFilters(prev => ({
      ...prev,
      attributes: prev.attributes.filter(
        attr => !(attr.slug === attributeSlug && attr.value === valueSlug)
      )
    }));
  };

  return (
    <div className="product-filters">
      {/* Model Filter */}
      <div>
        <label>Model</label>
        <select 
          value={filters.model}
          onChange={(e) => setFilters({...filters, model: e.target.value})}
        >
          <option value="">All Models</option>
          <option value="celsi-wool-felt">Celsi Wool Felt</option>
          <option value="another-model">Another Model</option>
        </select>
      </div>

      {/* Gender Filter */}
      <div>
        <label>Gender</label>
        <select 
          value={filters.gender}
          onChange={(e) => setFilters({...filters, gender: e.target.value})}
        >
          <option value="">All</option>
          <option value="MEN">Men</option>
          <option value="WOMEN">Women</option>
          <option value="UNISEX">Unisex</option>
          <option value="KIDS">Kids</option>
          <option value="BABY">Baby</option>
        </select>
      </div>

      {/* Color Attribute Filter (checkbox example) */}
      <div>
        <label>Color</label>
        <div>
          <label>
            <input
              type="checkbox"
              checked={filters.attributes.some(a => a.slug === 'color' && a.value === 'grey')}
              onChange={(e) => {
                if (e.target.checked) {
                  addAttributeFilter('color', 'grey');
                } else {
                  removeAttributeFilter('color', 'grey');
                }
              }}
            />
            Grey
          </label>
          <label>
            <input
              type="checkbox"
              checked={filters.attributes.some(a => a.slug === 'color' && a.value === 'black')}
              onChange={(e) => {
                if (e.target.checked) {
                  addAttributeFilter('color', 'black');
                } else {
                  removeAttributeFilter('color', 'black');
                }
              }}
            />
            Black
          </label>
        </div>
      </div>

      {/* Price Range */}
      <div>
        <label>Price Range (NPR)</label>
        <input
          type="number"
          placeholder="Min"
          value={filters.min_price}
          onChange={(e) => setFilters({...filters, min_price: e.target.value})}
        />
        <input
          type="number"
          placeholder="Max"
          value={filters.max_price}
          onChange={(e) => setFilters({...filters, max_price: e.target.value})}
        />
      </div>

      {/* Sort */}
      <div>
        <label>Sort By</label>
        <select 
          value={filters.ordering}
          onChange={(e) => setFilters({...filters, ordering: e.target.value})}
        >
          <option value="newest">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="name_asc">Name: A to Z</option>
          <option value="name_desc">Name: Z to A</option>
        </select>
      </div>
    </div>
  );
}

// Usage in product list component
export function ProductListPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleFilterChange = async (queryString) => {
    setLoading(true);
    try {
      const response = await fetch(
        `https://nyanopan.onrender.com/api/v1/products/?${queryString}`
      );
      const data = await response.json();
      setProducts(data.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <ProductFilters onFilterChange={handleFilterChange} />
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="product-grid">
          {products.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Response Format

### Product List Response

```json
{
  "success": true,
  "message": "Products retrieved successfully.",
  "data": [
    {
      "id": "uuid",
      "name": "Grey Wool Felt Slippers",
      "slug": "grey-wool-felt-slippers",
      "gender": "WOMEN",
      "category": {
        "id": "uuid",
        "name": "Indoor Slippers",
        "slug": "indoor-slippers"
      },
      "model": {
        "id": "uuid",
        "name": "Celsi Wool Felt",
        "slug": "celsi-wool-felt"
      },
      "is_featured": true,
      "price_range": {
        "min_price": "3,500.00",
        "max_price": "4,200.00"
      },
      "primary_image": {
        "url": "https://...",
        "title": "Grey Wool Felt Slippers",
        "alt": "..."
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Performance Notes

### Optimized Queries

The filter system uses:
- Database indexes on frequently filtered fields
- `.distinct()` to avoid duplicate results
- Active-only filtering (is_active=True)

### Best Practices

1. **Use specific filters** - More filters = fewer results = faster queries
2. **Paginate results** - Add `?page=1&page_size=20` for large result sets
3. **Cache filter options** - Fetch available attributes/values once, cache on frontend
4. **Debounce search input** - Wait for user to stop typing before filtering

---

## Testing the Filters

### Test Model Filter

```bash
curl "https://nyanopan.onrender.com/api/v1/products/?model=celsi-wool-felt"
```

### Test Attribute Filter (Single)

```bash
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey"
```

### Test Attribute Filter (Multiple OR)

```bash
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey&attribute=color:black"
```

### Test Attribute Filter (Multiple AND)

```bash
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey&attribute=size:large"
```

### Test Combined Filters

```bash
curl "https://nyanopan.onrender.com/api/v1/products/?model=celsi-wool-felt&attribute=color:grey&gender=WOMEN&ordering=price_asc"
```

---

## Summary

✅ **Filter by model** - `?model=celsi-wool-felt`  
✅ **Filter by attributes** - `?attribute=color:grey&attribute=size:large`  
✅ **Multiple values (OR)** - `?attribute=color:grey&attribute=color:black`  
✅ **Different attributes (AND)** - `?attribute=color:grey&attribute=size:large`  
✅ **Combine all filters** - Mix and match as needed  
✅ **Search and sort** - Full text search + flexible sorting  

The filtering system is now powerful enough to handle complex product catalog requirements! 🎉
