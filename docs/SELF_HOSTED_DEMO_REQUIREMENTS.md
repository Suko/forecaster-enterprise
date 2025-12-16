# Self-Hosted Full-Data Demo - Requirements & Analysis

**Goal:** Create a fully self-contained frontend demo that works without any backend, can be deployed as static files, and includes full realistic data.

---

## ✅ Is It Possible?

**Yes, absolutely.** Nuxt 4 supports Static Site Generation (SSG), which means you can:
- Pre-render all pages at build time
- Include all demo data as static JSON files
- Mock all API endpoints client-side
- Deploy to any static hosting (Netlify, Vercel, GitHub Pages, S3, etc.)
- No backend, database, or server required

---

## 📋 What's Required

### 1. **Data Requirements** (Full Dataset)

You need to export and include the following data as JSON files:

#### Dashboard Data
- **File:** `public/demo-data/dashboard.json`
- **Contains:**
  - KPI metrics (inventory value, SKU counts, understocked/overstocked)
  - Top 5 understocked products (with DIR, stockout risk)
  - Top 5 overstocked products (with DIR)
  - Trend data for charts (90+ days of historical data)

#### Inventory/Products Data
- **File:** `public/demo-data/products.json`
- **Contains:**
  - Full product list (200+ SKUs for realistic demo)
  - Each product: `item_id`, `product_name`, `stock_on_hand`, `dir`, `inventory_value`, `status`, `supplier`, `category`
  - Sales velocity (7-day, 30-day)
  - Stockout risk percentage

#### Recommendations Data
- **File:** `public/demo-data/recommendations.json`
- **Contains:**
  - Full recommendations list (50+ recommendations)
  - Each recommendation: `item_id`, `type` (REORDER, URGENT, REDUCE_ORDER, etc.), `priority`, `reason`, `recommended_quantity`, `recommended_date`

#### Forecast Data (for Product Detail Views)
- **File:** `public/demo-data/forecasts.json`
- **Contains:**
  - Forecast data for key products (10-20 products)
  - Historical sales (90+ days)
  - Forecast predictions (30-90 days ahead)
  - Confidence intervals (upper/lower bounds)
  - Estimated stockout dates

#### Trend Chart Data
- **File:** `public/demo-data/trends.json`
- **Contains:**
  - Inventory value trend (daily, 90+ days)
  - Sales velocity trend (daily, 90+ days)
  - Stock levels trend (daily, 90+ days)

#### Supporting Data
- **Locations:** `public/demo-data/locations.json`
- **Suppliers:** `public/demo-data/suppliers.json`
- **Purchase Orders (Cart):** `public/demo-data/cart.json`

**Estimated Total Data Size:** 2-5 MB (compressed JSON)

---

### 2. **Code Changes Required**

#### A. Mock API Layer
Replace all server routes (`server/api/*.ts`) with client-side mocks:

**Option 1: Client-Side API Mocks (Recommended)**
- Create `app/composables/useDemoApi.ts`
- All API calls return data from JSON files
- No server routes needed

**Option 2: Static Server Routes**
- Keep server routes but return static data
- Works in SSG mode if data is pre-loaded

#### B. Authentication Bypass
- **File:** `app/composables/useDemoAuth.ts`
- Mock user session (hardcoded demo user)
- Skip login page or auto-login
- No JWT validation needed

#### C. Build Configuration
- **File:** `nuxt.config.ts`
- Enable SSG mode: `ssr: false` or `nitro.prerender.routes`
- Configure static generation
- Set base URL for deployment

#### D. Data Loading Strategy
- **Option 1:** Load all data at app startup (fast, but larger initial load)
- **Option 2:** Lazy load per page (smaller initial load, but requires loading states)
- **Recommended:** Hybrid - load dashboard data upfront, lazy load inventory/recommendations

---

### 3. **Build & Deployment**

#### Build Process
```bash
# Generate static site
npm run generate

# Output: .output/public/ (static files)
```

#### Deployment Options
- **Netlify:** Drag & drop `.output/public` folder
- **Vercel:** Connect repo, auto-deploys on push
- **GitHub Pages:** Push to `gh-pages` branch
- **S3 + CloudFront:** Upload to S3 bucket
- **Any static host:** Just upload the files

**No server, database, or backend required.**

---

## 🎯 Demo Data Requirements (Detailed)

### Dashboard Data Structure
```json
{
  "metrics": {
    "total_inventory_value": "2900000",
    "total_skus": 200,
    "understocked_count": 23,
    "overstocked_count": 95,
    "understocked_value": "450000",
    "overstocked_value": "1200000"
  },
  "top_understocked": [...],
  "top_overstocked": [...]
}
```

### Products Data Structure
```json
[
  {
    "item_id": "M5_HOUSEHOLD_1_334",
    "product_name": "Product Name",
    "stock_on_hand": 45,
    "dir": 1.3,
    "inventory_value": 1250.50,
    "status": "understocked",
    "stockout_risk": 0.944,
    "sales_velocity_7d": 12,
    "sales_velocity_30d": 48,
    "supplier": "Supplier Name",
    "category": "HOUSEHOLD"
  },
  ...
]
```

### Recommendations Data Structure
```json
[
  {
    "item_id": "M5_HOUSEHOLD_1_334",
    "type": "REORDER",
    "priority": "HIGH",
    "reason": "Stockout risk 94.4%, DIR 1.3 days",
    "recommended_quantity": 150,
    "recommended_date": "2025-02-01",
    "current_stock": 45,
    "inventory_value": 1250.50
  },
  ...
]
```

### Forecast Data Structure
```json
{
  "M5_HOUSEHOLD_1_334": {
    "historical": [
      { "date": "2024-10-01", "value": 12 },
      ...
    ],
    "forecast": [
      {
        "date": "2025-02-01",
        "value": 15,
        "lower": 10,
        "upper": 20
      },
      ...
    ],
    "estimated_stockout_date": "2025-02-05",
    "recommended_reorder_window": {
      "start": "2025-01-28",
      "end": "2025-02-01"
    }
  }
}
```

---

## 📊 Data Export Process

### From Production/Staging Database

1. **Export Dashboard Data:**
   ```sql
   -- Run forecasting queries
   -- Export results to JSON
   ```

2. **Export Products:**
   ```sql
   SELECT * FROM products WHERE client_id = 'demo-client-id';
   -- Export to JSON
   ```

3. **Export Recommendations:**
   ```sql
   SELECT * FROM order_planning_recommendations WHERE client_id = 'demo-client-id';
   -- Export to JSON
   ```

4. **Export Forecast Data:**
   ```sql
   SELECT * FROM forecast_results WHERE client_id = 'demo-client-id';
   -- Export to JSON
   ```

5. **Export Trend Data:**
   ```sql
   -- Aggregate ts_demand_daily for trend charts
   -- Export to JSON
   ```

### Data Sanitization
- Remove sensitive data (real customer names, prices if needed)
- Ensure data is realistic but anonymized
- Validate JSON structure matches frontend types

---

## 🔧 Implementation Approach

### Phase 1: Data Export (1-2 days)
1. Create export scripts from database
2. Generate JSON files with full demo dataset
3. Validate data structure matches TypeScript types
4. Compress/minify JSON files

### Phase 2: Mock API Layer (2-3 days)
1. Create `useDemoApi.ts` composable
2. Replace all `$fetch('/api/...')` calls with demo data
3. Add loading states (simulate network delay)
4. Handle filtering/sorting client-side

### Phase 3: Authentication Bypass (1 day)
1. Create `useDemoAuth.ts` composable
2. Auto-login with demo user
3. Skip login page or show demo banner
4. Mock user session

### Phase 4: Build Configuration (1 day)
1. Configure Nuxt for SSG
2. Test static generation
3. Optimize bundle size
4. Test all pages work offline

### Phase 5: Testing & Polish (1-2 days)
1. Test all features work with static data
2. Verify filtering/sorting works
3. Test chart interactions
4. Optimize load times
5. Add demo mode indicator

**Total Estimated Time:** 6-9 days

---

## ⚠️ Limitations & Considerations

### What Won't Work
- ❌ **Real-time updates** - Data is static
- ❌ **User actions that modify data** - Add to cart, dismiss recommendations (can be simulated with localStorage)
- ❌ **Search/filter with backend** - All filtering must be client-side
- ❌ **Authentication** - Bypassed (demo mode only)
- ❌ **Settings changes** - Read-only (can use localStorage for demo)

### What Can Be Simulated
- ✅ **Add to cart** - Use localStorage, show animations
- ✅ **Dismiss recommendations** - Use localStorage, filter out dismissed items
- ✅ **Filtering/Sorting** - Client-side (AG Grid handles this)
- ✅ **Chart interactions** - Fully functional (Chart.js works client-side)
- ✅ **Navigation** - Fully functional (Vue Router works client-side)

### Performance Considerations
- **Initial Load:** 2-5 MB of JSON data (acceptable for demo)
- **Lazy Loading:** Load inventory/recommendations on-demand
- **Caching:** Browser caches JSON files after first load
- **Compression:** Gzip JSON files (reduces size by 70-80%)

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All demo data exported and validated
- [ ] All API calls mocked with static data
- [ ] Authentication bypassed (demo mode)
- [ ] All pages tested in static mode
- [ ] Bundle size optimized
- [ ] Images/assets optimized
- [ ] Demo mode indicator added

### Build
- [ ] Run `npm run generate`
- [ ] Verify `.output/public` contains all files
- [ ] Test locally with `npm run preview`

### Deployment
- [ ] Upload `.output/public` to hosting
- [ ] Configure redirects (SPA routing)
- [ ] Test all routes work
- [ ] Verify demo data loads correctly
- [ ] Test on mobile devices

### Post-Deployment
- [ ] Share demo URL
- [ ] Monitor for errors
- [ ] Collect feedback
- [ ] Update demo data periodically

---

## 📁 File Structure

```
frontend/
├── public/
│   └── demo-data/
│       ├── dashboard.json
│       ├── products.json
│       ├── recommendations.json
│       ├── forecasts.json
│       ├── trends.json
│       ├── locations.json
│       ├── suppliers.json
│       └── cart.json
├── app/
│   ├── composables/
│   │   ├── useDemoApi.ts      # Mock API layer
│   │   └── useDemoAuth.ts      # Mock authentication
│   └── pages/
│       └── ...                 # All pages work with demo data
└── nuxt.config.ts              # SSG configuration
```

---

## 🎯 Demo Mode Features

### Visual Indicators
- **Demo Banner:** "Demo Mode - All data is static"
- **Watermark (optional):** Subtle "DEMO" text
- **No Login Required:** Auto-login with demo user

### Functional Features
- ✅ All pages accessible
- ✅ All filters/sorting work
- ✅ All charts interactive
- ✅ Add to cart (localStorage)
- ✅ Dismiss recommendations (localStorage)
- ✅ Navigation fully functional

### Non-Functional
- ❌ No real-time updates
- ❌ No data persistence (except localStorage)
- ❌ No backend validation
- ❌ No actual purchases/orders

---

## 💡 Alternative: Hybrid Approach

Instead of fully static, you could:

1. **Keep Backend for Demo**
   - Deploy backend + frontend together
   - Use demo database with full data
   - Still self-hosted, but requires server
   - **Pros:** Full functionality, real-time updates
   - **Cons:** Requires server, more complex deployment

2. **CDN + Edge Functions**
   - Static frontend on CDN
   - Edge functions for API mocking
   - **Pros:** Fast, scalable
   - **Cons:** Requires edge function platform (Vercel, Netlify)

3. **Static + API Gateway**
   - Static frontend
   - API Gateway with cached responses
   - **Pros:** Best of both worlds
   - **Cons:** More complex setup

---

## 📝 Summary

### ✅ Feasible: Yes
- Nuxt 4 supports SSG
- All features can work with static data
- Client-side filtering/sorting works
- Charts work client-side

### ⏱️ Effort: 6-9 days
- Data export: 1-2 days
- Mock API layer: 2-3 days
- Auth bypass: 1 day
- Build config: 1 day
- Testing: 1-2 days

### 📦 Deliverable
- Static HTML/JS/CSS files
- JSON data files (2-5 MB)
- Deployable to any static host
- No backend required
- Fully functional demo

### 🎯 Use Cases
- Sales demos (offline)
- Client presentations
- Marketing website integration
- Trade show demos
- Investor pitches

---

**Last Updated:** 2025-01-27

