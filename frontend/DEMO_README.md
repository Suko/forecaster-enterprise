# Self-Hosted Demo Deployment Guide

This guide explains how to build and deploy a fully self-contained static demo of the Forecaster Enterprise application.

## Overview

The demo mode creates a static website that:
- ✅ Works without any backend server
- ✅ Includes full realistic data (200 products, 50 recommendations, etc.)
- ✅ All features work (filtering, sorting, charts, navigation)
- ✅ Can be deployed to any static hosting (Netlify, Vercel, GitHub Pages, S3, etc.)
- ✅ No database or API required

## Quick Start

### 1. Generate Demo Data

```bash
npm run demo:data
```

This creates JSON files in `public/demo-data/` with:
- Dashboard data
- 200 products
- 50 recommendations
- Trend charts (90 days)
- Forecast data (10 products)
- Cart data

### 2. Build Static Site

```bash
npm run generate:demo
```

This builds a static site with demo mode enabled. Output is in `.output/public/`.

### 3. Deploy

Upload the contents of `.output/public/` to any static host:

**Netlify:**
```bash
# Drag & drop .output/public folder to Netlify
```

**Vercel:**
```bash
vercel --prod
```

**GitHub Pages:**
```bash
# Push .output/public to gh-pages branch
```

**S3 + CloudFront:**
```bash
aws s3 sync .output/public s3://your-bucket-name
```

## Demo Mode Features

### What Works
- ✅ All pages (Dashboard, Inventory, Recommendations, Settings)
- ✅ Filtering and sorting (client-side)
- ✅ Interactive charts with zoom/pan
- ✅ Add to cart (uses localStorage)
- ✅ Dismiss recommendations (uses localStorage)
- ✅ Navigation
- ✅ Dark mode toggle
- ✅ All UI interactions

### What Doesn't Work
- ❌ Real-time updates (data is static)
- ❌ Data persistence (except localStorage)
- ❌ Actual API calls
- ❌ User authentication (auto-logged in as demo user)

## Testing Locally

### Test Demo Mode in Development

```bash
# Start dev server with demo mode
NUXT_PUBLIC_DEMO_MODE=true npm run dev
```

Or add `?demo=true` to any URL to enable demo mode.

### Test Static Build

```bash
# Build static site
npm run generate:demo

# Preview locally
npm run preview
```

## Demo Data Structure

All demo data is in `public/demo-data/`:

- `dashboard.json` - KPI metrics, top products
- `products.json` - 200 products with full details
- `recommendations.json` - 50 recommendations
- `trends.json` - 90 days of trend data
- `forecasts.json` - Forecast data for 10 products
- `cart.json` - Empty cart (initial state)

## Customization

### Update Demo Data

1. Edit `scripts/generate-demo-data.js`
2. Run `npm run demo:data` to regenerate
3. Rebuild: `npm run generate:demo`

### Change Demo User

Edit `app/composables/useDemoAuth.ts`:

```typescript
const demoUser = {
  email: "your-demo@email.com",
  name: "Your Demo User",
  role: "admin",
};
```

## Environment Variables

- `NUXT_PUBLIC_DEMO_MODE=true` - Enables demo mode
- Set this when building: `NUXT_PUBLIC_DEMO_MODE=true npm run generate`

## File Sizes

- Total demo data: ~2-5 MB (JSON files)
- Build output: ~500 KB - 2 MB (compressed)
- All assets: ~5-10 MB total

## Troubleshooting

### Demo data not loading
- Check that `public/demo-data/` files exist
- Verify files are included in build output
- Check browser console for errors

### Build fails
- Ensure all dependencies are installed: `npm install`
- Check for TypeScript errors: `npm run lint`
- Try cleaning build cache: `rm -rf .output .nuxt`

### Pages not working
- Verify demo mode is enabled: Check for demo banner at top of page
- Check browser console for errors
- Ensure all routes are pre-rendered

## Production Deployment

For production demo deployment:

1. **Generate fresh data:**
   ```bash
   npm run demo:data
   ```

2. **Build static site:**
   ```bash
   npm run generate:demo
   ```

3. **Test locally:**
   ```bash
   npm run preview
   ```

4. **Deploy `.output/public/` to hosting**

5. **Configure redirects** (for SPA routing):
   - Netlify: `_redirects` file
   - Vercel: `vercel.json`
   - S3: CloudFront with error pages

## Support

For issues or questions, see:
- [Self-Hosted Demo Requirements](../../docs/SELF_HOSTED_DEMO_REQUIREMENTS.md)
- [Demo Wow Features](../../docs/DEMO_WOW_FEATURES.md)

