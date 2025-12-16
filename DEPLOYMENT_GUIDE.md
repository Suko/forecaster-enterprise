# Deployment Guide for Demo Branch

This guide explains how to deploy the demo branch online for live demonstrations.

## 🚀 Quick Deploy Options

### Option 1: Cloudflare Pages (Recommended)

Cloudflare Pages offers fast global CDN, free SSL, and excellent performance for Nuxt.js applications.

#### Steps:

1. **Go to [dash.cloudflare.com](https://dash.cloudflare.com)** and sign in
2. **Navigate to**: Pages → Create a project
3. **Connect to Git**: Select GitHub and authorize Cloudflare
4. **Select repository**: `Suko/forecaster-enterprise`
5. **Configure the project**:
   - **Project name**: `forecaster-enterprise-demo`
   - **Production branch**: `demo` (or `main` for production)
   - **Framework preset**: Nuxt.js (auto-detected)
   - **Build command**: `cd frontend && bun run build` (or `cd frontend && npm run build`)
   - **Build output directory**: `frontend/.output/public`
   - **Root directory**: Leave empty (or set to `frontend` if needed)
6. **Environment Variables**:
   - Click "Add variable"
   - Add `NUXT_PUBLIC_DEMO_MODE` = `true`
   - Add any other environment variables as needed
7. **Deploy!**

#### Branch-Specific Deployment:

- **Production**: Deploy from `main` branch
- **Demo**: Deploy from `demo` branch
  - In Cloudflare Pages, go to Settings → Builds & deployments
  - Configure branch deployments
  - Each branch gets its own preview URL

#### Custom Domain (Optional):

- In Cloudflare Pages project → Custom domains
- Add a custom domain like `demo.forecaster-enterprise.com`
- Cloudflare automatically configures SSL

#### Benefits of Cloudflare Pages:

- ✅ **Free tier** with generous limits
- ✅ **Global CDN** - fast worldwide
- ✅ **Automatic HTTPS** - SSL certificates
- ✅ **Preview deployments** - for every PR
- ✅ **Instant rollbacks** - one-click revert
- ✅ **Analytics** - built-in page views
- ✅ **No credit card required** for free tier

---

### Option 2: Vercel

Vercel is another excellent option for Nuxt.js applications.

#### Steps:

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub
2. **Click "Add New Project"**
3. **Import your repository**: `Suko/forecaster-enterprise`
4. **Configure the project**:
   - **Framework Preset**: Nuxt.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `bun run build` (or `npm run build` if using npm)
   - **Output Directory**: `.output/public` (Nuxt 3 default)
   - **Install Command**: `bun install` (or `npm install`)
5. **Environment Variables** (if needed):
   - `NUXT_PUBLIC_DEMO_MODE=true` (for demo mode)
6. **Deploy!**

---

### Option 3: Netlify

1. **Go to [netlify.com](https://netlify.com)** and sign in with GitHub
2. **Click "Add new site" → "Import an existing project"**
3. **Select your repository**: `Suko/forecaster-enterprise`
4. **Build settings**:
   - **Base directory**: `frontend`
   - **Build command**: `bun run build` (or `npm run build`)
   - **Publish directory**: `frontend/.output/public`
5. **Deploy!**

#### Netlify Configuration File

Create `netlify.toml` in the root:

```toml
[build]
  base = "frontend"
  command = "bun run build"
  publish = "frontend/.output/public"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

### Option 3: GitHub Pages (Static)

For static deployment:

1. **Build the static site**:
   ```bash
   cd frontend
   bun run generate
   ```

2. **Push to GitHub Pages**:
   - Go to repository Settings → Pages
   - Select source: `demo` branch
   - Select folder: `frontend/dist` (or `.output/public`)

**Note**: This requires the app to be fully static (no server-side features).

---

### Option 4: Self-Hosted (Docker)

If you have a server:

1. **Build Docker image**:
   ```bash
   cd frontend
   docker build -t forecaster-demo .
   ```

2. **Run container**:
   ```bash
   docker run -p 3000:3000 forecaster-demo
   ```

3. **Use a reverse proxy** (nginx/traefik) for HTTPS

---

## 📋 Pre-Deployment Checklist

- [ ] All changes committed and pushed to `demo` branch
- [ ] Environment variables configured
- [ ] Build command tested locally (`bun run build`)
- [ ] Demo mode enabled (`NUXT_PUBLIC_DEMO_MODE=true`)
- [ ] No hardcoded localhost URLs
- [ ] API endpoints work (if using external APIs)

---

## 🔧 Environment Variables

Set these in your deployment platform:

```bash
# Demo Mode
NUXT_PUBLIC_DEMO_MODE=true

# API Base URL (if using external API)
NUXT_PUBLIC_API_BASE_URL=https://api.example.com

# Other environment variables as needed
```

---

## 🌐 Deployment URLs

After deployment, you'll get URLs like:

- **Cloudflare Pages**: `forecaster-enterprise-demo.pages.dev`
- **Vercel**: `forecaster-enterprise-demo.vercel.app`
- **Netlify**: `forecaster-enterprise-demo.netlify.app`
- **Custom Domain**: `demo.forecaster-enterprise.com`

---

## 🔄 Updating the Demo

To update the live demo:

1. Make changes on `demo` branch
2. Commit and push:
   ```bash
   git add .
   git commit -m "Update demo features"
   git push origin demo
   ```
3. Deployment platform will automatically rebuild and deploy

---

## 🐛 Troubleshooting

### Build Fails

- Check build logs in deployment platform
- Test build locally: `cd frontend && bun run build`
- Ensure all dependencies are in `package.json`
- **Cloudflare Pages**: Check that build command includes `cd frontend` if root is repo root

### App Doesn't Load

- Check browser console for errors
- Verify environment variables are set
- Check if demo mode is enabled
- **Cloudflare Pages**: Verify `_redirects` file is in output directory for SPA routing

### API Errors

- Ensure API endpoints are accessible
- Check CORS settings if using external APIs
- Verify API base URL in environment variables

### Cloudflare Pages Specific

- **Build timeout**: Cloudflare Pages has a 15-minute build limit (free tier)
- **Output directory**: Ensure `.output/public` is correct for Nuxt 3
- **Environment variables**: Must be set in Cloudflare Pages dashboard (not in code)
- **Custom domain**: DNS must point to Cloudflare (use Cloudflare nameservers)
- **Preview deployments**: Each branch/PR gets a unique URL automatically

---

## 📝 Notes

- **Demo branch** is separate from `main` - safe to experiment
- **Automatic deployments** happen on every push to `demo` branch
- **Preview deployments** available for pull requests
- **Custom domains** can be added for professional demos

---

## 🎯 Recommended Setup

For best results, use **Cloudflare Pages** with:
- Automatic deployments from `demo` branch
- Custom domain (optional)
- Preview deployments for PRs
- Environment variables configured

This gives you:
- ✅ Fast global CDN (Cloudflare's network)
- ✅ Automatic HTTPS (free SSL certificates)
- ✅ Easy rollbacks (one-click revert)
- ✅ Preview URLs for testing (every PR gets a URL)
- ✅ Free tier with generous limits
- ✅ Built-in analytics
- ✅ DDoS protection included
- ✅ No credit card required

