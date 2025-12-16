# Deployment Guide for Demo Branch

This guide explains how to deploy the demo branch online for live demonstrations.

## 🚀 Quick Deploy Options

### Option 1: Vercel (Recommended - Easiest)

Vercel is the easiest option for Nuxt.js applications.

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

#### Branch-Specific Deployment:

- **Production**: Deploy from `main` branch
- **Demo**: Deploy from `demo` branch
  - In Vercel dashboard, go to Settings → Git
  - Add `demo` branch for automatic deployments
  - Or create a separate project for demo branch

#### Custom Domain (Optional):

- In Vercel project settings → Domains
- Add a custom domain like `demo.forecaster-enterprise.com`

---

### Option 2: Netlify

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

### App Doesn't Load

- Check browser console for errors
- Verify environment variables are set
- Check if demo mode is enabled

### API Errors

- Ensure API endpoints are accessible
- Check CORS settings if using external APIs
- Verify API base URL in environment variables

---

## 📝 Notes

- **Demo branch** is separate from `main` - safe to experiment
- **Automatic deployments** happen on every push to `demo` branch
- **Preview deployments** available for pull requests
- **Custom domains** can be added for professional demos

---

## 🎯 Recommended Setup

For best results, use **Vercel** with:
- Automatic deployments from `demo` branch
- Custom domain (optional)
- Preview deployments for PRs
- Environment variables configured

This gives you:
- ✅ Fast global CDN
- ✅ Automatic HTTPS
- ✅ Easy rollbacks
- ✅ Preview URLs for testing

