# Product Filter - Real-World Examples

## Quick Reference

```
Base URL: https://nyanopan.onrender.com/api/v1/products/
```

---

## Example 1: Model Collection Page

**Scenario:** User clicks on "Celsi Wool Felt" collection

**URL:**
```
GET /api/v1/products/?model=celsi-wool-felt&ordering=newest
```

**Frontend Code:**
```jsx
<Link href="/collections/celsi-wool-felt">
  <h3>Celsi Wool Felt Collection</h3>
</Link>

// Collection page component
function CollectionPage({ modelSlug }) {
  const [products, setProducts] = useState([]);
  
  useEffect(() => {
    fetch(`/api/v1/products/?model=${modelSlug}&ordering=newest`)
      .then(res => res.json())
      .then(data => setProducts(data.data));
  }, [modelSlug]);
  
  return <ProductGrid products={products} />;
}
```

---

## Example 2: Color Filter Sidebar

**Scenario:** User selects grey and black colors

**URL:**
```
GET /api/v1/products/?attribute=color:grey&attribute=color:black
```

**Frontend Code:**
```jsx
function ColorFilter({ selectedColors, onChange }) {
  const colors = [
    { slug: 'grey', name: 'Grey', hex: '#808080' },
    { slug: 'black', name: 'Black', hex: '#000000' },
    { slug: 'beige', name: 'Beige', hex: '#F5F5DC' }
  ];
  
  const toggleColor = (colorSlug) => {
    const newColors = selectedColors.includes(colorSlug)
      ? selectedColors.filter(c => c !== colorSlug)
      : [...selectedColors, colorSlug];
    onChange(newColors);
  };
  
  return (
    <div className="color-filter">
      <h4>Color</h4>
      {colors.map(color => (
        <label key={color.slug}>
          <input
            type="checkbox"
            checked={selectedColors.includes(color.slug)}
            onChange={() => toggleColor(color.slug)}
          />
          <span 
            className="color-swatch"
            style={{ backgroundColor: color.hex }}
          />
          {color.name}
        </label>
      ))}
    </div>
  );
}

// Build URL with selected colors
const params = new URLSearchParams();
selectedColors.forEach(color => {
  params.append('attribute', `color:${color}`);
});
const url = `/api/v1/products/?${params.toString()}`;
// Result: /api/v1/products/?attribute=color:grey&attribute=color:black
```

---

## Example 3: Shop by Gender + Model

**Scenario:** Women's section of a specific collection

**URL:**
```
GET /api/v1/products/?model=celsi-wool-felt&gender=WOMEN&ordering=price_asc
```

**Frontend Code:**
```jsx
function GenderModelPage() {
  return (
    <div>
      <h1>Women's Celsi Wool Felt</h1>
      <ProductList 
        filters={{
          model: 'celsi-wool-felt',
          gender: 'WOMEN',
          ordering: 'price_asc'
        }}
      />
    </div>
  );
}
```

---

## Example 4: Advanced Filter UI

**Scenario:** User applies multiple filters from sidebar

**URL:**
```
GET /api/v1/products/?category=indoor-slippers&gender=WOMEN&attribute=color:grey&attribute=size:large&sole_type=RUBBER&min_price=2000&max_price=5000&ordering=price_asc
```

**Frontend Code:**
```jsx
function ProductFilters() {
  const [filters, setFilters] = useState({
    category: 'indoor-slippers',
    gender: 'WOMEN',
    colors: ['grey'],
    sizes: ['large'],
    sole_type: 'RUBBER',
    min_price: 2000,
    max_price: 5000,
    ordering: 'price_asc'
  });
  
  const buildUrl = () => {
    const params = new URLSearchParams();
    
    if (filters.category) params.append('category', filters.category);
    if (filters.gender) params.append('gender', filters.gender);
    if (filters.sole_type) params.append('sole_type', filters.sole_type);
    if (filters.min_price) params.append('min_price', filters.min_price);
    if (filters.max_price) params.append('max_price', filters.max_price);
    if (filters.ordering) params.append('ordering', filters.ordering);
    
    // Add color attributes
    filters.colors.forEach(color => {
      params.append('attribute', `color:${color}`);
    });
    
    // Add size attributes
    filters.sizes.forEach(size => {
      params.append('attribute', `size:${size}`);
    });
    
    return `/api/v1/products/?${params.toString()}`;
  };
  
  return (
    <aside className="filters">
      {/* Category */}
      <FilterGroup title="Category">
        <select 
          value={filters.category}
          onChange={e => setFilters({...filters, category: e.target.value})}
        >
          <option value="">All Categories</option>
          <option value="indoor-slippers">Indoor Slippers</option>
          <option value="outdoor-slippers">Outdoor Slippers</option>
        </select>
      </FilterGroup>
      
      {/* Gender */}
      <FilterGroup title="Gender">
        {['MEN', 'WOMEN', 'UNISEX', 'KIDS'].map(gender => (
          <label key={gender}>
            <input
              type="radio"
              name="gender"
              value={gender}
              checked={filters.gender === gender}
              onChange={e => setFilters({...filters, gender: e.target.value})}
            />
            {gender}
          </label>
        ))}
      </FilterGroup>
      
      {/* Colors */}
      <FilterGroup title="Color">
        {['grey', 'black', 'beige'].map(color => (
          <label key={color}>
            <input
              type="checkbox"
              checked={filters.colors.includes(color)}
              onChange={e => {
                const newColors = e.target.checked
                  ? [...filters.colors, color]
                  : filters.colors.filter(c => c !== color);
                setFilters({...filters, colors: newColors});
              }}
            />
            {color}
          </label>
        ))}
      </FilterGroup>
      
      {/* Sizes */}
      <FilterGroup title="Size">
        {['small', 'medium', 'large', 'x-large'].map(size => (
          <label key={size}>
            <input
              type="checkbox"
              checked={filters.sizes.includes(size)}
              onChange={e => {
                const newSizes = e.target.checked
                  ? [...filters.sizes, size]
                  : filters.sizes.filter(s => s !== size);
                setFilters({...filters, sizes: newSizes});
              }}
            />
            {size}
          </label>
        ))}
      </FilterGroup>
      
      {/* Sole Type */}
      <FilterGroup title="Sole Type">
        <label>
          <input
            type="radio"
            name="sole_type"
            value="LEATHER"
            checked={filters.sole_type === 'LEATHER'}
            onChange={e => setFilters({...filters, sole_type: e.target.value})}
          />
          Leather
        </label>
        <label>
          <input
            type="radio"
            name="sole_type"
            value="RUBBER"
            checked={filters.sole_type === 'RUBBER'}
            onChange={e => setFilters({...filters, sole_type: e.target.value})}
          />
          Rubber
        </label>
      </FilterGroup>
      
      {/* Price Range */}
      <FilterGroup title="Price Range">
        <input
          type="number"
          placeholder="Min"
          value={filters.min_price}
          onChange={e => setFilters({...filters, min_price: e.target.value})}
        />
        <input
          type="number"
          placeholder="Max"
          value={filters.max_price}
          onChange={e => setFilters({...filters, max_price: e.target.value})}
        />
      </FilterGroup>
      
      {/* Sort */}
      <FilterGroup title="Sort By">
        <select 
          value={filters.ordering}
          onChange={e => setFilters({...filters, ordering: e.target.value})}
        >
          <option value="newest">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="name_asc">Name: A-Z</option>
        </select>
      </FilterGroup>
    </aside>
  );
}
```

---

## Example 5: "More Like This" Section

**Scenario:** Product detail page showing similar products

**URL:**
```
GET /api/v1/products/?model=celsi-wool-felt&attribute=color:grey&exclude={current_product_id}
```

**Frontend Code:**
```jsx
function SimilarProducts({ currentProduct }) {
  const [similar, setSimilar] = useState([]);
  
  useEffect(() => {
    const params = new URLSearchParams({
      model: currentProduct.model.slug,
      ordering: 'newest'
    });
    
    // Add color attribute if product has one
    if (currentProduct.primary_color) {
      params.append('attribute', `color:${currentProduct.primary_color}`);
    }
    
    fetch(`/api/v1/products/?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
        // Filter out current product
        const filtered = data.data.filter(p => p.id !== currentProduct.id);
        setSimilar(filtered.slice(0, 4)); // Show 4 similar products
      });
  }, [currentProduct]);
  
  return (
    <section className="similar-products">
      <h2>You Might Also Like</h2>
      <ProductGrid products={similar} />
    </section>
  );
}
```

---

## Example 6: Quick Filter Buttons

**Scenario:** Quick filter chips above product grid

**URL (when clicking "Grey"):**
```
GET /api/v1/products/?attribute=color:grey
```

**Frontend Code:**
```jsx
function QuickFilters() {
  const [activeFilters, setActiveFilters] = useState([]);
  
  const quickFilters = [
    { label: 'Grey', type: 'attribute', value: 'color:grey' },
    { label: 'Black', type: 'attribute', value: 'color:black' },
    { label: 'Indoor', type: 'usage_location', value: 'INSIDE' },
    { label: 'Outdoor', type: 'usage_location', value: 'OUTSIDE' },
    { label: 'Under 5000', type: 'max_price', value: '5000' },
  ];
  
  const toggleFilter = (filter) => {
    const key = `${filter.type}:${filter.value}`;
    const newFilters = activeFilters.includes(key)
      ? activeFilters.filter(f => f !== key)
      : [...activeFilters, key];
    setActiveFilters(newFilters);
  };
  
  return (
    <div className="quick-filters">
      {quickFilters.map(filter => (
        <button
          key={filter.label}
          className={activeFilters.includes(`${filter.type}:${filter.value}`) ? 'active' : ''}
          onClick={() => toggleFilter(filter)}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}
```

---

## Example 7: Breadcrumb Navigation

**Scenario:** Category > Model > Color filtered view

**URL:**
```
GET /api/v1/products/?category=indoor-slippers&model=celsi-wool-felt&attribute=color:grey
```

**Breadcrumb Display:**
```
Home > Indoor Slippers > Celsi Wool Felt > Grey
```

**Frontend Code:**
```jsx
function Breadcrumbs({ filters }) {
  const buildUrl = (upToLevel) => {
    const params = new URLSearchParams();
    if (upToLevel >= 1 && filters.category) params.append('category', filters.category);
    if (upToLevel >= 2 && filters.model) params.append('model', filters.model);
    if (upToLevel >= 3 && filters.color) params.append('attribute', `color:${filters.color}`);
    return `/products?${params.toString()}`;
  };
  
  return (
    <nav className="breadcrumbs">
      <Link href="/">Home</Link>
      {filters.category && (
        <>
          <span>/</span>
          <Link href={buildUrl(1)}>Indoor Slippers</Link>
        </>
      )}
      {filters.model && (
        <>
          <span>/</span>
          <Link href={buildUrl(2)}>Celsi Wool Felt</Link>
        </>
      )}
      {filters.color && (
        <>
          <span>/</span>
          <span className="current">Grey</span>
        </>
      )}
    </nav>
  );
}
```

---

## Example 8: Filter Persistence (URL State)

**Scenario:** User applies filters, shares URL with friend

**URL:**
```
https://nyanopan.com/products?model=celsi-wool-felt&attribute=color:grey&attribute=size:large&ordering=price_asc
```

**Frontend Code (Next.js):**
```jsx
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

function ProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState([]);
  
  // Parse filters from URL
  const filters = {
    model: router.query.model || '',
    attributes: Array.isArray(router.query.attribute) 
      ? router.query.attribute 
      : router.query.attribute ? [router.query.attribute] : [],
    ordering: router.query.ordering || 'newest'
  };
  
  // Update URL when filters change
  const updateFilters = (newFilters) => {
    const params = new URLSearchParams();
    if (newFilters.model) params.append('model', newFilters.model);
    newFilters.attributes.forEach(attr => params.append('attribute', attr));
    if (newFilters.ordering) params.append('ordering', newFilters.ordering);
    
    router.push(`/products?${params.toString()}`, undefined, { shallow: true });
  };
  
  // Fetch products when URL changes
  useEffect(() => {
    const apiUrl = `/api/v1/products/?${new URLSearchParams(router.query).toString()}`;
    fetch(apiUrl)
      .then(res => res.json())
      .then(data => setProducts(data.data));
  }, [router.query]);
  
  return (
    <div>
      <Filters filters={filters} onChange={updateFilters} />
      <ProductGrid products={products} />
    </div>
  );
}
```

---

## Example 9: Mobile Filter Sheet

**Scenario:** Mobile user opens filter bottom sheet

**Frontend Code:**
```jsx
function MobileFilterSheet({ isOpen, onClose, onApply }) {
  const [tempFilters, setTempFilters] = useState({
    colors: [],
    sizes: [],
    priceRange: { min: '', max: '' }
  });
  
  const applyFilters = () => {
    const params = new URLSearchParams();
    tempFilters.colors.forEach(color => {
      params.append('attribute', `color:${color}`);
    });
    tempFilters.sizes.forEach(size => {
      params.append('attribute', `size:${size}`);
    });
    if (tempFilters.priceRange.min) {
      params.append('min_price', tempFilters.priceRange.min);
    }
    if (tempFilters.priceRange.max) {
      params.append('max_price', tempFilters.priceRange.max);
    }
    
    onApply(params.toString());
    onClose();
  };
  
  return (
    <Sheet isOpen={isOpen} onClose={onClose}>
      <div className="filter-sheet">
        <header>
          <h2>Filters</h2>
          <button onClick={onClose}>×</button>
        </header>
        
        <div className="filter-content">
          {/* Color chips */}
          <FilterSection title="Color">
            {['grey', 'black', 'beige'].map(color => (
              <Chip
                key={color}
                label={color}
                selected={tempFilters.colors.includes(color)}
                onClick={() => {
                  setTempFilters(prev => ({
                    ...prev,
                    colors: prev.colors.includes(color)
                      ? prev.colors.filter(c => c !== color)
                      : [...prev.colors, color]
                  }));
                }}
              />
            ))}
          </FilterSection>
          
          {/* Size chips */}
          <FilterSection title="Size">
            {['small', 'medium', 'large'].map(size => (
              <Chip
                key={size}
                label={size}
                selected={tempFilters.sizes.includes(size)}
                onClick={() => {
                  setTempFilters(prev => ({
                    ...prev,
                    sizes: prev.sizes.includes(size)
                      ? prev.sizes.filter(s => s !== size)
                      : [...prev.sizes, size]
                  }));
                }}
              />
            ))}
          </FilterSection>
          
          {/* Price slider */}
          <FilterSection title="Price Range">
            <PriceSlider
              min={0}
              max={10000}
              value={[tempFilters.priceRange.min, tempFilters.priceRange.max]}
              onChange={(values) => {
                setTempFilters(prev => ({
                  ...prev,
                  priceRange: { min: values[0], max: values[1] }
                }));
              }}
            />
          </FilterSection>
        </div>
        
        <footer>
          <button onClick={() => setTempFilters({ colors: [], sizes: [], priceRange: {} })}>
            Clear All
          </button>
          <button className="primary" onClick={applyFilters}>
            Apply Filters
          </button>
        </footer>
      </div>
    </Sheet>
  );
}
```

---

## Summary

These examples demonstrate:

✅ **Model filtering** - Collection pages  
✅ **Attribute filtering** - Color, size, material filters  
✅ **Multiple attributes** - Complex filter combinations  
✅ **URL persistence** - Shareable filter states  
✅ **Mobile-friendly** - Bottom sheet filters  
✅ **Quick filters** - One-click filter chips  
✅ **Breadcrumbs** - Navigation with filters  
✅ **Similar products** - Filtered recommendations  

All examples work with the updated API! 🎉
