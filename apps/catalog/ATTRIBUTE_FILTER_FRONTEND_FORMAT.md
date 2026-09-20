# Attribute Filter - Frontend ID-Based Format Support

## Issue Report from Frontend

The frontend team reported that attribute filtering was not working. Analysis showed:

### Problem 1: Backend didn't support frontend's format
- Frontend sends: `?attribute_{attribute_id}={value_id}`
- Backend only supported: `?attribute=name:name`

### Problem 2: Data consistency concern (FALSE ALARM)
- Frontend reported different IDs between `/api/v1/attributes/` and product variants
- **This is EXPECTED behavior** - they are different entities:
  - `/api/v1/attributes/` returns `AttributeValue` IDs
  - Product variants use `ProductVariantOption` IDs (different table)
  - Products link to attributes via `ProductAttributeValue` table

---

## Solution Implemented

Added support for **frontend's ID-based format** while keeping the name-based format working.

### File: `apps/catalog/filters.py`

**Key Changes:**

1. **Added `__init__` method** to store request for later use
2. **Override `qs` property** to handle dynamic `attribute_{id}={value_id}` parameters
3. **Keep existing `filter_by_attribute` method** for name-based filtering

---

## How It Works Now

### Architecture

```
Frontend Request
    ↓
?attribute_{attr_id}={value_id}
    ↓
ProductFilter.qs property
    ↓
Filters ProductAttributeValue table
    ↓
Returns products with matching attribute values
```

### Data Model

```
Product
  ↓ (has many)
ProductAttributeValue
  ├─ attribute_id (FK to Attribute)
  ├─ attribute_value_id (FK to AttributeValue)
  └─ is_active (boolean)
```

**The filter queries `ProductAttributeValue` to find products with specific attribute values.**

---

## Supported Formats

### Format 1: ID-Based (Frontend Format) ✅ NEW

**Query String:**
```
?attribute_{attribute_uuid}={value_uuid}
```

**Examples:**
```bash
# Single attribute
GET /api/v1/products/?attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=332dd17b-7d92-417f-b5b4-8169d23fb417

# Multiple values for same attribute (OR logic)
GET /api/v1/products/?attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=332dd17b&attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=e478df01

# Multiple different attributes (AND logic)
GET /api/v1/products/?attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=332dd17b&attribute_12345678-1234-1234-1234-123456789012=fdb6572a
```

**How it works:**
1. Filter parses all `attribute_*` parameters
2. Extracts attribute ID from parameter name
3. Gets value ID(s) from parameter value
4. Queries `ProductAttributeValue` table
5. Returns products matching the criteria

**SQL Query (simplified):**
```sql
SELECT DISTINCT products.*
FROM products
JOIN product_attribute_values pav ON products.id = pav.product_id
WHERE pav.attribute_id = 'af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164'
  AND pav.attribute_value_id = '332dd17b-7d92-417f-b5b4-8169d23fb417'
  AND pav.is_active = TRUE;
```

### Format 2: Name-Based (Alternative Format) ✅ EXISTING

**Query String:**
```
?attribute=attribute_name:value_name
```

**Examples:**
```bash
# Single attribute
GET /api/v1/products/?attribute=color:grey

# Multiple attributes
GET /api/v1/products/?attribute=color:grey&attribute=size:large
```

**How it works:**
1. Filter calls `filter_by_attribute` method
2. Splits `name:name` format
3. Queries by attribute name and value name (case-insensitive)

---

## Frontend Integration

### Step 1: Fetch Attributes

```javascript
// Fetch attributes with their values
const response = await fetch('/api/v1/attributes/');
const data = await response.json();

/*
Response structure:
{
  "data": [
    {
      "id": "af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164",  // ← Attribute ID
      "name": "Color",
      "values": [
        {
          "id": "332dd17b-7d92-417f-b5b4-8169d23fb417",  // ← Value ID
          "name": "Black"
        },
        {
          "id": "e478df01-e3c1-4267-bc8d-d79f6b45f4e1",  // ← Value ID
          "name": "Blue"
        }
      ]
    },
    {
      "id": "12345678-1234-1234-1234-123456789012",  // ← Attribute ID
      "name": "Size",
      "values": [
        {
          "id": "fdb6572a-db68-4e8e-9858-40d9e38f8853",  // ← Value ID
          "name": "L"
        }
      ]
    }
  ]
}
*/
```

### Step 2: Build Filter URL

```javascript
// Build URL with attribute_{id}={value_id} format
const buildFilterUrl = (selectedFilters) => {
  const params = new URLSearchParams();
  
  // Add other filters
  if (filters.category) params.append('category', filters.category);
  if (filters.gender) params.append('gender', filters.gender);
  
  // Add attribute filters using ID format
  selectedFilters.forEach(filter => {
    const paramName = `attribute_${filter.attributeId}`;
    params.append(paramName, filter.valueId);
  });
  
  return `/api/v1/products/?${params.toString()}`;
};

// Example usage
const filters = [
  { 
    attributeId: 'af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164',  // Color attribute
    valueId: '332dd17b-7d92-417f-b5b4-8169d23fb417'       // Black value
  },
  { 
    attributeId: '12345678-1234-1234-1234-123456789012',  // Size attribute
    valueId: 'fdb6572a-db68-4e8e-9858-40d9e38f8853'       // L value
  }
];

const url = buildFilterUrl(filters);
// Result: /api/v1/products/?attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=332dd17b-7d92-417f-b5b4-8169d23fb417&attribute_12345678-1234-1234-1234-123456789012=fdb6572a-db68-4e8e-9858-40d9e38f8853
```

### Step 3: Fetch Filtered Products

```javascript
const fetchFilteredProducts = async (filters) => {
  const url = buildFilterUrl(filters);
  const response = await fetch(url);
  const data = await response.json();
  return data.data;  // Array of products
};
```

### React Example

```jsx
function ProductFilterSidebar({ attributes, onFilterChange }) {
  const [selectedFilters, setSelectedFilters] = useState([]);
  
  const toggleFilter = (attributeId, valueId) => {
    const exists = selectedFilters.some(
      f => f.attributeId === attributeId && f.valueId === valueId
    );
    
    if (exists) {
      // Remove filter
      setSelectedFilters(prev => 
        prev.filter(f => !(f.attributeId === attributeId && f.valueId === valueId))
      );
    } else {
      // Add filter
      setSelectedFilters(prev => [...prev, { attributeId, valueId }]);
    }
  };
  
  useEffect(() => {
    onFilterChange(selectedFilters);
  }, [selectedFilters]);
  
  return (
    <div className="filter-sidebar">
      {attributes.map(attr => (
        <div key={attr.id} className="filter-group">
          <h4>{attr.name}</h4>
          {attr.values.map(value => (
            <label key={value.id}>
              <input
                type="checkbox"
                checked={selectedFilters.some(
                  f => f.attributeId === attr.id && f.valueId === value.id
                )}
                onChange={() => toggleFilter(attr.id, value.id)}
              />
              {value.name}
            </label>
          ))}
        </div>
      ))}
    </div>
  );
}
```

---

## Filter Logic

### Single Attribute, Single Value

```
GET /products/?attribute_<attr_id>=<value_id>
→ Returns products with that specific attribute value
```

### Single Attribute, Multiple Values (OR)

```
GET /products/?attribute_<attr_id>=<value_id1>&attribute_<attr_id>=<value_id2>
→ Returns products with value1 OR value2 for that attribute
```

**Implementation:**
```python
# Uses Q objects for OR logic
Q(attribute_id=attr_id, value_id=value_id1) | 
Q(attribute_id=attr_id, value_id=value_id2)
```

### Multiple Attributes (AND)

```
GET /products/?attribute_<attr_id1>=<value_id>&attribute_<attr_id2>=<value_id>
→ Returns products with BOTH attribute values
```

**Implementation:**
```python
# Chained filters for AND logic
queryset.filter(attr1_criteria).filter(attr2_criteria)
```

---

## Data Consistency Clarification

### What the Frontend Reported

> "Attribute value IDs don't match between `/api/v1/attributes/` and product variants"

### Why This is Expected

The system has **three separate ID spaces**:

1. **AttributeValue IDs** - Global reusable attribute values
   - Returned by `/api/v1/attributes/`
   - Used in `ProductAttributeValue` table
   - Used for **product-level attributes** (color, material)

2. **ProductVariantOption IDs** - Variant-specific values
   - Returned in product variant details
   - Links variants to `AttributeValue`
   - Used for **variant selection** (size, color per variant)

3. **ProductAttributeValue IDs** - Product-attribute associations
   - Links products to attribute values
   - Has its own ID (not shown to frontend)
   - This is what the filter queries

### Example Data Flow

```
Product: "Wool Slippers"
  ↓
ProductAttributeValue (ID: xxx)
  ├─ attribute_id: "color-attribute-id"
  ├─ attribute_value_id: "grey-value-id"  ← This ID comes from /api/v1/attributes/
  └─ feature_image: "grey-slippers.jpg"
  
Product Variant: "Wool Slippers - Size L"
  ↓
ProductVariantOption (ID: yyy)
  ├─ attribute_id: "size-attribute-id"
  └─ attribute_value_id: "L-value-id"  ← This ID ALSO comes from /api/v1/attributes/
```

**Both use the same `AttributeValue` IDs from `/api/v1/attributes/`!**

If they appear different, it might be:
- Different attributes (Color vs Size)
- Different values (Black vs Blue)
- Looking at different products

---

## Testing

### Create Test Data

```python
# In Django shell or seed script
from apps.catalog.models import Attribute, AttributeValue, Product, ProductAttributeValue

# Create Color attribute
color_attr = Attribute.objects.create(name="Color", requires_image=True)
black = AttributeValue.objects.create(attribute=color_attr, name="Black")
grey = AttributeValue.objects.create(attribute=color_attr, name="Grey")

# Create Size attribute
size_attr = Attribute.objects.create(name="Size")
small = AttributeValue.objects.create(attribute=size_attr, name="Small")
large = AttributeValue.objects.create(attribute=size_attr, name="Large")

# Assign to product
product = Product.objects.first()
ProductAttributeValue.objects.create(
    product=product,
    attribute=color_attr,
    attribute_value=black
)
ProductAttributeValue.objects.create(
    product=product,
    attribute=size_attr,
    attribute_value=large
)

print(f"Color attribute ID: {color_attr.id}")
print(f"Black value ID: {black.id}")
print(f"Size attribute ID: {size_attr.id}")
print(f"Large value ID: {large.id}")
```

### Test ID-Based Filter

```bash
# Filter by color=black
curl "http://localhost:8000/api/v1/products/?attribute_{color_attr_id}={black_id}"

# Filter by color=black AND size=large
curl "http://localhost:8000/api/v1/products/?attribute_{color_attr_id}={black_id}&attribute_{size_attr_id}={large_id}"
```

### Test Name-Based Filter

```bash
# Filter by color=black
curl "http://localhost:8000/api/v1/products/?attribute=color:black"

# Filter by color=black AND size=large
curl "http://localhost:8000/api/v1/products/?attribute=color:black&attribute=size:large"
```

---

## Summary

✅ **Backend now supports frontend's ID-based format:** `?attribute_{attr_id}={value_id}`  
✅ **Still supports name-based format:** `?attribute=name:name`  
✅ **OR logic for multiple values of same attribute**  
✅ **AND logic for different attributes**  
✅ **Data consistency is correct** - AttributeValue IDs are consistent  
✅ **Ready for frontend integration**  

The attribute filtering now works with the frontend's expected format! 🎉
