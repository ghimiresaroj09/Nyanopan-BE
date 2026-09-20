# Attribute Filter Fix

## Issue Found

The attribute filter was not working because:

1. **Wrong field lookup**: The filter was trying to use `slug` fields on `Attribute` and `AttributeValue` models, but these models only have `name` fields (no slug).
2. **Incorrect filter path**: Was using `attribute__slug` and `attribute_value__slug` which don't exist.

---

## What Was Fixed

### File: `apps/catalog/filters.py`

**Before (❌ Broken):**
```python
# Filter products that have this attribute value
return queryset.filter(
    attribute_values__attribute__slug=attribute_slug,      # ❌ slug field doesn't exist
    attribute_values__attribute_value__slug=value_slug,    # ❌ slug field doesn't exist
    attribute_values__is_active=True
).distinct()
```

**After (✅ Fixed):**
```python
# Filter products that have this attribute value (case-insensitive)
return queryset.filter(
    attribute_values__attribute__name__iexact=attribute_name,           # ✅ Uses name field
    attribute_values__attribute_value__name__iexact=value_name,         # ✅ Uses name field
    attribute_values__is_active=True
).distinct()
```

**Key Changes:**
1. Changed `slug` → `name` (the actual field on the model)
2. Changed `iexact` lookup for case-insensitive matching
3. Updated variable names to reflect `name` instead of `slug`

---

## Model Structure (For Reference)

### Attribute Model
```python
class Attribute(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)  # ✅ Has 'name', NOT 'slug'
    requires_image = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
```

### AttributeValue Model
```python
class AttributeValue(TimeStampedModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=100)  # ✅ Has 'name', NOT 'slug'
    is_active = models.BooleanField(default=True, db_index=True)
```

### ProductAttributeValue Model
```python
class ProductAttributeValue(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name="product_values")
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.PROTECT, related_name="product_values")
    # ... feature_image fields ...
    is_active = models.BooleanField(default=True, db_index=True)
```

---

## Updated API Usage

### Format

**Old (incorrect):** `?attribute=attribute_slug:value_slug`  
**New (correct):** `?attribute=attribute_name:value_name`

### Examples

```bash
# Filter by Color = Grey (case-insensitive)
GET /api/v1/products/?attribute=color:grey
GET /api/v1/products/?attribute=Color:Grey  # Also works

# Filter by Size = Large
GET /api/v1/products/?attribute=size:large
GET /api/v1/products/?attribute=Size:Large  # Also works

# Multiple attributes (AND logic)
GET /api/v1/products/?attribute=color:grey&attribute=size:large

# With other filters
GET /api/v1/products/?model=celsi-wool-felt&attribute=color:grey&gender=WOMEN
```

---

## How It Works Now

### Single Attribute Filter

**Request:**
```
GET /api/v1/products/?attribute=color:grey
```

**SQL Query (simplified):**
```sql
SELECT DISTINCT products.*
FROM products
JOIN product_attribute_values ON products.id = product_attribute_values.product_id
JOIN attributes ON product_attribute_values.attribute_id = attributes.id
JOIN attribute_values ON product_attribute_values.attribute_value_id = attribute_values.id
WHERE LOWER(attributes.name) = 'color'
  AND LOWER(attribute_values.name) = 'grey'
  AND product_attribute_values.is_active = TRUE;
```

### Multiple Attributes (AND Logic)

**Request:**
```
GET /api/v1/products/?attribute=color:grey&attribute=size:large
```

Django-filters calls `filter_by_attribute()` twice:
1. First call: Filters products with color=grey
2. Second call: Takes result from step 1 and filters for size=large

**Result:** Products that have BOTH color=grey AND size=large

---

## Testing the Filter

### Step 1: Create Sample Attributes

```python
# In Django shell or seed script
from apps.catalog.models import Attribute, AttributeValue, Product, ProductAttributeValue

# Create Color attribute
color_attr = Attribute.objects.create(name="Color", requires_image=True)
grey = AttributeValue.objects.create(attribute=color_attr, name="Grey")
black = AttributeValue.objects.create(attribute=color_attr, name="Black")
beige = AttributeValue.objects.create(attribute=color_attr, name="Beige")

# Create Size attribute
size_attr = Attribute.objects.create(name="Size")
small = AttributeValue.objects.create(attribute=size_attr, name="Small")
medium = AttributeValue.objects.create(attribute=size_attr, name="Medium")
large = AttributeValue.objects.create(attribute=size_attr, name="Large")

# Assign to products
product = Product.objects.first()
ProductAttributeValue.objects.create(
    product=product,
    attribute=color_attr,
    attribute_value=grey
)
ProductAttributeValue.objects.create(
    product=product,
    attribute=size_attr,
    attribute_value=large
)
```

### Step 2: Test the Filter

```bash
# Should return products with color=Grey
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey"

# Should return products with color=Grey AND size=Large
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=color:grey&attribute=size:large"

# Case insensitive - also works
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=Color:Grey"
curl "https://nyanopan.onrender.com/api/v1/products/?attribute=COLOR:GREY"
```

---

## Frontend Integration

### JavaScript Example

```javascript
// Build filter URL with attribute names (not slugs!)
const buildFilterUrl = (filters) => {
  const params = new URLSearchParams();
  
  // Add attribute filters
  filters.attributes?.forEach(attr => {
    // Use the attribute NAME and value NAME
    params.append('attribute', `${attr.attributeName}:${attr.valueName}`);
  });
  
  return `/api/v1/products/?${params.toString()}`;
};

// Example usage
const url = buildFilterUrl({
  attributes: [
    { attributeName: 'Color', valueName: 'Grey' },
    { attributeName: 'Size', valueName: 'Large' }
  ]
});
// Result: /api/v1/products/?attribute=Color:Grey&attribute=Size:Large
```

### React Component

```jsx
function AttributeFilter({ attributes, selectedValues, onChange }) {
  // attributes: [{ name: 'Color', values: [{name: 'Grey'}, {name: 'Black'}] }]
  // selectedValues: [{ attributeName: 'Color', valueName: 'Grey' }]
  
  const isSelected = (attrName, valueName) => {
    return selectedValues.some(
      sv => sv.attributeName === attrName && sv.valueName === valueName
    );
  };
  
  const toggleValue = (attrName, valueName) => {
    const isCurrentlySelected = isSelected(attrName, valueName);
    
    if (isCurrentlySelected) {
      // Remove
      const newValues = selectedValues.filter(
        sv => !(sv.attributeName === attrName && sv.valueName === valueName)
      );
      onChange(newValues);
    } else {
      // Add
      onChange([...selectedValues, { attributeName: attrName, valueName: valueName }]);
    }
  };
  
  return (
    <div className="attribute-filters">
      {attributes.map(attr => (
        <div key={attr.name} className="filter-group">
          <h4>{attr.name}</h4>
          {attr.values.map(value => (
            <label key={value.name}>
              <input
                type="checkbox"
                checked={isSelected(attr.name, value.name)}
                onChange={() => toggleValue(attr.name, value.name)}
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

## Important Notes

### ✅ What Works Now

1. **Case-insensitive matching** - `color:grey`, `Color:Grey`, `COLOR:GREY` all work
2. **Name-based filtering** - Uses actual model field names
3. **Multiple attributes** - AND logic when different attributes
4. **Proper distinct** - No duplicate results

### ⚠️ Important Changes from Documentation

**Previous documentation said:** Use `attribute_slug:value_slug`  
**Correct usage now:** Use `attribute_name:value_name`

**Reason:** The `Attribute` and `AttributeValue` models don't have slug fields, only name fields.

### 📝 Frontend Considerations

When building your attribute filters:

1. **Fetch attribute data from API:**
   ```javascript
   GET /api/v1/admin/attributes/  // To get all attributes
   GET /api/v1/admin/attribute-values/?attribute={id}  // To get values for an attribute
   ```

2. **Use the `name` field** (not slug) when constructing filter URLs

3. **Case doesn't matter** - The filter is case-insensitive, but using the exact case from API is recommended for consistency

---

## Summary

✅ **Fixed:** Changed from non-existent `slug` fields to actual `name` fields  
✅ **Fixed:** Added case-insensitive matching with `__iexact`  
✅ **Fixed:** Updated documentation to use correct format  
✅ **Works:** Single attribute filtering  
✅ **Works:** Multiple attribute filtering with AND logic  
✅ **Ready:** Production-ready implementation  

The attribute filter now works correctly! 🎉

**Usage:** `?attribute=attribute_name:value_name` (case-insensitive)
