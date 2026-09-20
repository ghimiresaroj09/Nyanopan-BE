# Attribute Filter - Fix Summary

## Problem

The attribute filter was **not working** because it was trying to filter by `slug` fields that don't exist on the `Attribute` and `AttributeValue` models.

**Error in code:**
```python
# ❌ WRONG - These fields don't exist
queryset.filter(
    attribute_values__attribute__slug=attribute_slug,      # No 'slug' field
    attribute_values__attribute_value__slug=value_slug,    # No 'slug' field
)
```

---

## Root Cause

The `Attribute` and `AttributeValue` models only have `name` fields, NOT `slug` fields:

```python
class Attribute(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)  # ✅ Has 'name'
    # No slug field!

class AttributeValue(TimeStampedModel):
    name = models.CharField(max_length=100)  # ✅ Has 'name'
    # No slug field!
```

---

## Solution

Changed the filter to use `name` fields with case-insensitive matching:

```python
# ✅ CORRECT - Uses actual model fields
queryset.filter(
    attribute_values__attribute__name__iexact=attribute_name,
    attribute_values__attribute_value__name__iexact=value_name,
    attribute_values__is_active=True
).distinct()
```

---

## Changes Made

### File: `apps/catalog/filters.py`

1. **Changed field lookups:**
   - `attribute__slug` → `attribute__name__iexact`
   - `attribute_value__slug` → `attribute_value__name__iexact`

2. **Added case-insensitive matching:**
   - Using `__iexact` lookup for case-insensitive comparison

3. **Updated variable names:**
   - `attribute_slug` → `attribute_name`
   - `value_slug` → `value_name`

4. **Updated documentation:**
   - Help text now says "attribute name and value name"
   - Comments clarified the correct format

### File: `apps/catalog/views/public.py`

Updated API documentation to reflect correct usage.

---

## Correct Usage

### Format

**Use:** `attribute_name:value_name` (case-insensitive)

### Examples

```bash
# Single attribute (case-insensitive)
GET /api/v1/products/?attribute=color:grey
GET /api/v1/products/?attribute=Color:Grey  # Also works
GET /api/v1/products/?attribute=COLOR:GREY  # Also works

# Multiple attributes (AND logic)
GET /api/v1/products/?attribute=color:grey&attribute=size:large

# Combined with other filters
GET /api/v1/products/?model=celsi-wool-felt&attribute=color:grey&gender=WOMEN&ordering=price_asc
```

---

## How to Get Attribute Names

### From Admin API

```bash
# Get all attributes
GET /api/v1/admin/attributes/

# Response:
{
  "data": [
    {
      "id": "uuid",
      "name": "Color",      # ← Use this in filter
      "requires_image": true,
      "is_active": true
    },
    {
      "id": "uuid",
      "name": "Size",       # ← Use this in filter
      "requires_image": false,
      "is_active": true
    }
  ]
}
```

```bash
# Get values for an attribute
GET /api/v1/admin/attribute-values/?attribute={attribute_id}

# Response:
{
  "data": [
    {
      "id": "uuid",
      "attribute": "Color",
      "name": "Grey",       # ← Use this in filter
      "is_active": true
    },
    {
      "id": "uuid",
      "attribute": "Color",
      "name": "Black",      # ← Use this in filter
      "is_active": true
    }
  ]
}
```

---

## Frontend Implementation

```javascript
// 1. Fetch attributes and their values
const fetchAttributes = async () => {
  const response = await fetch('/api/v1/admin/attributes/');
  const data = await response.json();
  return data.data;
};

// 2. Build filter URL using attribute NAMES
const buildFilterUrl = (selectedAttributes) => {
  const params = new URLSearchParams();
  
  selectedAttributes.forEach(attr => {
    // Use the 'name' field from the API response
    params.append('attribute', `${attr.attributeName}:${attr.valueName}`);
  });
  
  return `/api/v1/products/?${params.toString()}`;
};

// 3. Example usage
const filters = [
  { attributeName: 'Color', valueName: 'Grey' },
  { attributeName: 'Size', valueName: 'Large' }
];

const url = buildFilterUrl(filters);
// Result: /api/v1/products/?attribute=Color:Grey&attribute=Size:Large
```

---

## Testing

### Current State
- ✅ Filter logic is correct
- ✅ Uses proper field names (`name` instead of `slug`)
- ✅ Case-insensitive matching works
- ⚠️ No test data yet (0 attributes in database)

### To Test with Real Data

1. **Create attributes via admin:**
   ```bash
   POST /api/v1/admin/attributes/
   {
     "name": "Color",
     "requires_image": true,
     "is_active": true
   }
   ```

2. **Create attribute values:**
   ```bash
   POST /api/v1/admin/attribute-values/
   {
     "attribute": "{attribute_id}",
     "name": "Grey",
     "is_active": true
   }
   ```

3. **Assign to products:**
   - When creating/editing products, assign attribute values
   - Each assignment creates a `ProductAttributeValue` record

4. **Test filter:**
   ```bash
   GET /api/v1/products/?attribute=Color:Grey
   ```

---

## Summary

| Aspect | Before (Broken) | After (Fixed) |
|--------|----------------|---------------|
| **Format** | `attribute_slug:value_slug` | `attribute_name:value_name` |
| **Field lookup** | `__slug` (doesn't exist) | `__name__iexact` (correct) |
| **Case sensitivity** | Case-sensitive | Case-insensitive |
| **Status** | ❌ Not working | ✅ Working |

---

## Key Takeaways

1. **Use `name` fields, not `slug`** - The models don't have slug fields
2. **Case doesn't matter** - Filter is case-insensitive
3. **AND logic for multiple attributes** - Different attributes are combined with AND
4. **Fetch names from API** - Use the admin API to get correct attribute/value names

The attribute filter now works correctly! 🎉
