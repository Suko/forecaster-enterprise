# Deploy Demo to Cloudflare Pages

Complete guide for deploying the Forecaster Enterprise demo to Cloudflare Pages.

## Overview

This demo is a **frontend-only static site** that:
- ✅ Works without any backend server
- ✅ Includes full realistic data (200 products, 50 recommendations)
- ✅ All features work (filtering, sorting, charts, navigation)
- ✅ No database or API required
- ✅ Free hosting on Cloudflare Pages

---

## Quick Start

### 1. Generate Demo Data

**Important:** Demo data must be generated **before** deploying to Cloudflare. You have two options:

#### Option A: Generate Locally and Commit (Recommended)

Generate the data locally and commit the files to git:

```bash
cd frontend
bun run demo:data
git add public/demo-data/
git commit -m "Add demo data files"
git push
```

This creates JSON files in `public/demo-data/`:
- `dashboard.json` - KPI metrics, top products
- `products.json` - 200 products with full details
- `recommendations.json` - 50 recommendations
- `trends.json` - 90 days of trend data
- `forecasts.json` - Forecast data for 10 products
- `cart.json` - Empty cart (initial state)

**Total Size:** ~300 KB (uncompressed)

**Pros:** Files are versioned, faster builds, data is consistent
**Cons:** JSON files in git (but small size is acceptable)

#### Option B: Generate During Cloudflare Build

If you prefer not to commit JSON files, generate them during the build:

1. **Update build command in Cloudflare:**
   ```
   bun run demo:data && bun run build
   ```

2. **Ensure script is executable:**
   - The `demo:data` script is already in `package.json`
   - Cloudflare will run it automatically during build

**Pros:** No JSON files in git
**Cons:** Slightly longer build time, data regenerated each build

### 2. Test Locally

```bash
# Development with demo mode
NUXT_PUBLIC_DEMO_MODE=true bun run dev

# Or add ?demo=true to URL
# http://localhost:3000?demo=true

# Build and preview static site
bun run generate:demo
bun run preview
```

### 3. Deploy to Cloudflare Pages

#### Option A: Connect GitHub Repository

1. **Push code to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Demo branch ready for Cloudflare"
   git push origin demo
   ```

2. **Connect to Cloudflare Pages**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Navigate to **Pages** → **Create a project**
   - Select **Connect to Git**
   - Choose your repository and branch (e.g., `demo`)

3. **Configure Build Settings**
   
   Use these exact settings:
   
   - **Framework preset:** `Nuxt.js`
   - **Build command:** 
     - If demo data is committed: `bun run build`
     - If generating during build: `bun run demo:data && bun run build`
   - **Build output directory:** `.output/public`
   - **Root directory:** `frontend`
   - **Environment variables:**
     - `NUXT_PUBLIC_DEMO_MODE` = `true`

4. **Deploy**
   - Click **Save and Deploy**
   - Cloudflare will build and deploy automatically
   - Your demo will be live at `https://your-project.pages.dev`

#### Option B: Direct Upload (Manual)

1. **Build static site locally:**
   ```bash
   cd frontend
   NUXT_PUBLIC_DEMO_MODE=true bun run generate
   ```

2. **Upload to Cloudflare Pages:**
   - Go to Cloudflare Dashboard → Pages
   - Create a new project
   - Select **Upload assets**
   - Upload the contents of `.output/public/` folder

---

## Build Configuration

### Cloudflare Pages Settings

When connecting via Git, use these build settings:

| Setting | Value |
|---------|-------|
| **Framework preset** | Nuxt.js |
| **Build command** | `bun run build` (or `bun run demo:data && bun run build` if generating during build) |
| **Build output directory** | `.output/public` |
| **Root directory** | `frontend` |
| **Environment variable** | `NUXT_PUBLIC_DEMO_MODE=true` |

**Note:** If demo data files are already committed to git, use `bun run build`. If you want to generate data during build, use `bun run demo:data && bun run build`.

### Environment Variables

Add this environment variable in Cloudflare Pages:

- **Variable name:** `NUXT_PUBLIC_DEMO_MODE`
- **Value:** `true`

This enables demo mode which:
- Auto-logs in as demo user
- Uses static JSON data instead of API calls
- Shows demo banner in UI

---

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

---

## Customization

### Update Demo Data

1. Edit `frontend/scripts/generate-demo-data.js`
2. Regenerate data:
   ```bash
   cd frontend
   bun run demo:data
   ```
3. Commit and push - Cloudflare will auto-deploy

### Change Demo User

Edit `frontend/app/composables/useDemoAuth.ts`:

```typescript
const demoUser = {
  email: "your-demo@email.com",
  name: "Your Demo User",
  role: "admin",
};
```

---

## Troubleshooting

### Build Fails

**Issue:** Build command fails
- **Solution:** Ensure `bun` is available in Cloudflare's build environment
- **Alternative:** Use `npm run build` if bun is not available

**Issue:** Output directory not found
- **Solution:** Verify build output directory is `.output/public`
- **Check:** Run `bun run generate` locally and verify `.output/public/` exists

### Demo Data Not Loading

**Issue:** JSON files not found
- **Solution:** 
  - If using Option A (committed files): Ensure `public/demo-data/` files are committed to git
  - If using Option B (build-time generation): Ensure build command includes `bun run demo:data`
- **Check:** Verify files exist in `frontend/public/demo-data/` after build
- **Debug:** Check Cloudflare build logs to see if `demo:data` script ran successfully

**Issue:** Demo mode not enabled
- **Solution:** Verify `NUXT_PUBLIC_DEMO_MODE=true` is set in Cloudflare environment variables
- **Check:** Look for demo banner at top of page

### Pages Not Working (404 Errors)

**Issue:** Routes return 404
- **Solution:** Cloudflare Pages should auto-detect Nuxt.js and handle SPA routing
- **Check:** Verify Framework preset is set to "Nuxt.js"

---

## File Structure

```
forecaster_enterprise/
├── frontend/
│   ├── public/
│   │   └── demo-data/          # Demo data JSON files
│   │       ├── dashboard.json
│   │       ├── products.json
│   │       ├── recommendations.json
│   │       ├── trends.json
│   │       ├── forecasts.json
│   │       └── cart.json
│   ├── app/
│   │   ├── composables/
│   │   │   ├── useDemoApi.ts   # Mock API layer
│   │   │   ├── useDemoAuth.ts  # Demo authentication
│   │   │   └── useDemoMode.ts  # Demo mode detection
│   │   └── plugins/
│   │       └── demo-mode.client.ts  # Auto-initialize demo
│   ├── scripts/
│   │   └── generate-demo-data.js  # Data generation script
│   ├── nuxt.config.ts          # SSG configuration
│   └── package.json            # Build scripts
└── docs/
    └── CLOUDFLARE_HOSTING.md   # This file
```

---

## Performance

- **Initial Load:** ~300 KB (demo data) + ~2 MB (app bundle)
- **Total Size:** ~5-10 MB (compressed)
- **Load Time:** < 2 seconds on Cloudflare's CDN
- **Caching:** Browser caches JSON files after first load

---

## Continuous Deployment

Cloudflare Pages automatically:
- ✅ Builds on every push to connected branch
- ✅ Creates preview deployments for pull requests
- ✅ Deploys to production on merge
- ✅ Provides instant rollback

### Custom Domain

1. Go to **Pages** → Your project → **Custom domains**
2. Add your domain
3. Update DNS records as instructed
4. SSL certificate is automatically provisioned

---

## Support

For issues:
1. Check Cloudflare Pages build logs
2. Verify environment variables are set
3. Test build locally: `bun run generate:demo`
4. Check browser console for errors

---

**Last Updated:** 2025-01-27

