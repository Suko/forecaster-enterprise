# Forecaster Enterprise - Demo

**Frontend-only static demo** of the Forecaster Enterprise inventory forecasting platform.

This demo works **without any backend** - all data is static JSON files that are included in the build. Perfect for sales demos, client presentations, and marketing.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
bun install
```

### 2. Generate Demo Data

```bash
bun run demo:data
```

This creates JSON files in `public/demo-data/` with:
- Dashboard data (KPIs, metrics)
- 200 products with full details
- 50 recommendations
- Trend charts (90 days)
- Forecast data (10 products)

### 3. Run Development Server

```bash
# With demo mode enabled
NUXT_PUBLIC_DEMO_MODE=true bun run dev

# Or add ?demo=true to URL
# http://localhost:3000?demo=true
```

### 4. Deploy to Cloudflare Pages

See **[Cloudflare Hosting Guide](docs/CLOUDFLARE_HOSTING.md)** for complete deployment instructions.

**Quick deploy:**
1. Push code to GitHub
2. Connect repository to Cloudflare Pages
3. Set build settings:
   - Framework: Nuxt.js
   - Build command: `bun run build`
   - Output directory: `.output/public`
   - Root directory: `frontend`
   - Environment: `NUXT_PUBLIC_DEMO_MODE=true`

## Demo Features

### ✅ Fully Functional
- Dashboard with KPIs and interactive charts
- Inventory table with 200 products (filtering, sorting)
- Recommendations list with 50 items
- Interactive charts with zoom/pan
- Navigation between pages
- Dark mode toggle
- Settings pages (read-only)

### ✅ Simulated (localStorage)
- Add to cart
- Dismiss recommendations
- Cart persistence

### ❌ Not Available
- Real-time updates (data is static)
- Data persistence (except localStorage)
- Actual API calls
- User authentication (auto-logged in as demo user)

## Documentation

- **[Cloudflare Hosting Guide](docs/CLOUDFLARE_HOSTING.md)** - Complete deployment guide for Cloudflare Pages
- **[Demo Wow Features](docs/DEMO_WOW_FEATURES.md)** - UI features for demos

## Project Structure

```
forecaster_enterprise/
├── frontend/              # Nuxt 4 frontend application
│   ├── app/              # App directory (components, pages, composables)
│   ├── public/           # Static assets
│   │   └── demo-data/    # Demo data JSON files
│   ├── scripts/          # Data generation scripts
│   └── package.json      # Dependencies and scripts
└── docs/                 # Demo documentation
```

## Tech Stack

- **Frontend:** Nuxt 4 (Vue 3)
- **UI:** Nuxt UI + Tailwind CSS 4
- **Charts:** Chart.js with zoom/pan
- **Tables:** AG Grid
- **Build:** Static Site Generation (SSG)
- **Package Manager:** Bun

## Demo Data

All demo data is in `frontend/public/demo-data/`:
- `dashboard.json` - KPI metrics, top products
- `products.json` - 200 products with full details
- `recommendations.json` - 50 recommendations
- `trends.json` - 90 days of trend data
- `forecasts.json` - Forecast data for 10 products
- `cart.json` - Empty cart (initial state)

**Total Size:** ~300 KB (uncompressed)

## Environment Variables

- `NUXT_PUBLIC_DEMO_MODE=true` - Enables demo mode
- Set this when building: `NUXT_PUBLIC_DEMO_MODE=true bun run generate`

## Support

For issues or questions, see the documentation in the `docs/` folder.

---

**Note:** This is a demo branch with frontend-only static files. For the full application with backend, see the main branch.
