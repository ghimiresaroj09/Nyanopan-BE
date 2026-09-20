# Gender Field Made Optional

## Change Summary

The `gender` field on the `Product` model is now **optional** (nullable).

---

## What Changed

### Database Model

**File:** `apps/catalog/models.py`

**Before:**
```python
gender = models.CharField(max_length=10, choices=Gender.choices, db_index=True)
```

**After:**
```python
gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True, db_index=True)
```

### Migration

**File:** `apps/catalog/migrations/0009_make_gender_optional.py`

Applied migration that:
- Allows `gender` field to be `NULL` in the database
- Allows empty/blank values in forms and serializers

---

## Impact

### ✅ What Works Now

1. **Create products without gender:**
   ```json
   POST /api/v1/admin/products/
   {
     "name": "Universal Comfort Slippers",
     "model": "celsi-wool-felt",
     "category": "indoor-slippers",
     // gender field can be omitted
     "description": "..."
   }
   ```

2. **Update products to remove gender:**
   ```json
   PATCH /api/v1/admin/products/{id}/
   {
     "gender": null
   }
   ```

3. **Filter by gender (existing behavior):**
   ```bash
   GET /api/v1/products/?gender=UNISEX
   GET /api/v1/products/?gender=WOMEN
   # Products without gender won't appear in these filtered results
   ```

### 📋 API Response Examples

**Product with gender:**
```json
{
  "id": "...",
  "name": "Women's Wool Slippers",
  "gender": "WOMEN",
  "..."
}
```

**Product without gender:**
```json
{
  "id": "...",
  "name": "Universal Comfort Slippers",
  "gender": null,
  "..."
}
```

---

## Gender Choices (Unchanged)

The available gender values remain the same:

```python
class Gender(models.TextChoices):
    MEN = "MEN", "Men"
    WOMEN = "WOMEN", "Women"
    UNISEX = "UNISEX", "Unisex"
    KIDS = "KIDS", "Kids"
    BABY = "BABY", "Baby"
```

---

## Use Cases

### Gender-Neutral Products
Products that don't have a specific gender target:
- Universal sizing items
- Unisex designs (use `UNISEX` value)
- Products where gender distinction doesn't apply

### Legacy Products
- Existing products can have their gender removed
- Admin can set `gender: null` when updating

### Filtering Behavior
- Filter `?gender=WOMEN` returns only products where `gender="WOMEN"`
- Products with `gender=null` are excluded from gender-filtered results
- Without filter, all products (with or without gender) are returned

---

## Frontend Integration

### Admin Panel

**Create/Edit Product Form:**
```jsx
<select name="gender" optional>
  <option value="">-- No Gender --</option>
  <option value="MEN">Men</option>
  <option value="WOMEN">Women</option>
  <option value="UNISEX">Unisex</option>
  <option value="KIDS">Kids</option>
  <option value="BABY">Baby</option>
</select>
```

### Public Site

**Display Gender:**
```jsx
{product.gender && (
  <span className="gender-badge">
    {product.gender}
  </span>
)}
```

**Filter Products:**
```jsx
// Show gender filter only when relevant
<select onChange={(e) => filterByGender(e.target.value)}>
  <option value="">All Products</option>
  <option value="MEN">Men</option>
  <option value="WOMEN">Women</option>
  <option value="UNISEX">Unisex</option>
  <option value="KIDS">Kids</option>
  <option value="BABY">Baby</option>
</select>
```

---

## Database Index

The database index on the `gender` field is maintained for efficient filtering:

```python
indexes = [
    models.Index(fields=["gender", "is_active"]),
    # ... other indexes
]
```

Products with `gender=NULL` are still indexed and can be queried efficiently.

---

## Backward Compatibility

✅ **Existing products:** All existing products with gender values remain unchanged  
✅ **API responses:** Gender field still appears in responses (as `null` when not set)  
✅ **Filtering:** Gender filters continue to work exactly as before  
✅ **Admin panel:** Gender dropdown can now have "No Gender" option  

---

## Testing

### Test Creating Product Without Gender

```bash
curl -X POST https://nyanopan.onrender.com/api/v1/admin/products/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "model": "celsi-wool-felt",
    "category": "indoor-slippers",
    "description": "Test product without gender"
  }'
```

**Expected:** 201 Created with `"gender": null`

### Test Updating Product to Remove Gender

```bash
curl -X PATCH https://nyanopan.onrender.com/api/v1/admin/products/{id}/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gender": null
  }'
```

**Expected:** 200 OK with `"gender": null`

### Test Filtering

```bash
# Get all products (including null gender)
GET /api/v1/products/

# Get only women's products (excludes null gender)
GET /api/v1/products/?gender=WOMEN

# Get only products with no gender set
GET /api/v1/admin/products/?gender__isnull=true
```

---

## Summary

✅ Gender field is now **optional** on Product model  
✅ Migration applied: `0009_make_gender_optional`  
✅ API accepts products without gender  
✅ Backward compatible with existing products  
✅ Filtering behavior unchanged  
✅ Database index maintained for performance  

**Use case:** Create products that don't have a specific gender target, or update existing products to remove gender specification.
