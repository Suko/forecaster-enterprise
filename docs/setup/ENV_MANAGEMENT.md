# Environment Variables Management Guide

## 🎯 Local Testing vs Production

### **Local/Development Setup**
- Use simple passwords for easy testing
- Secrets can be in `.env` file (gitignored)
- Default values are acceptable
- Focus on functionality, not security

### **Production Setup**
- Use strong, unique passwords
- Secrets should be in secure secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never commit secrets to git
- Use environment-specific values
- Enable all security features

---

## 📝 Local Testing Configuration

### **Quick Setup for Docker Testing**

Your `.env` file should have these values for local testing:

```bash
# ==============================================================================
# LOCAL TESTING CONFIGURATION
# ==============================================================================

# ------------------------------------------------------------------------------
# Database Configuration (Local Docker)
# ------------------------------------------------------------------------------
DB_USER=postgres
DB_PASSWORD=postgres123                    # Simple password for local testing
DB_NAME=forecaster_enterprise

# ------------------------------------------------------------------------------
# Application Configuration
# ------------------------------------------------------------------------------
ENVIRONMENT=development                     # Use 'development' for local testing
DEBUG=true                                  # Enable debug for local testing

# JWT Secret Key - REQUIRED
# Generated with: openssl rand -hex 32
JWT_SECRET_KEY=0ebc0cac6a838232ffc36ed8f5ae7d6b4f2bff520771982a26f7e02a1e90f00f

# ------------------------------------------------------------------------------
# Admin User (created on first startup)
# ------------------------------------------------------------------------------
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123                     # Simple password for local testing
ADMIN_NAME=Admin User

# ------------------------------------------------------------------------------
# Frontend Configuration
# ------------------------------------------------------------------------------
# Nuxt Session Password - REQUIRED
# Generated with: openssl rand -hex 32
NUXT_SESSION_PASSWORD=398a0c4ad0515f8f1874cc97d64ee290a25ca8ec0f6f30ccad438af2a507845e

# Public API URL (what the browser uses to reach the backend)
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000

# ------------------------------------------------------------------------------
# License Configuration (Optional for local testing)
# ------------------------------------------------------------------------------
LICENSE_URL=
LICENSE_KEY=
CHECK_INTERVAL=3600
GRACE_PERIOD=172800

# ------------------------------------------------------------------------------
# First-Time Setup (Local Testing)
# ------------------------------------------------------------------------------
SETUP_TEST_DATA=true                        # Enable test data for local testing
CLIENT_NAME=Demo Client

# Path to CSV file (relative to project root)
CSV_PATH=./data/synthetic_data/synthetic_ecom_chronos2_demo.csv

# Optional test user
TEST_EMAIL=test@example.com
TEST_PASSWORD=testpassword123
TEST_NAME=Test User
```

---

## 🔧 How to Update Your .env File

### **Option 1: Manual Edit (Recommended for Testing)**

```bash
# 1. Open .env file
nano .env  # or use your preferred editor

# 2. Update these lines:
JWT_SECRET_KEY=0ebc0cac6a838232ffc36ed8f5ae7d6b4f2bff520771982a26f7e02a1e90f00f
NUXT_SESSION_PASSWORD=398a0c4ad0515f8f1874cc97d64ee290a25ca8ec0f6f30ccad438af2a507845e
DB_PASSWORD=postgres123
ADMIN_PASSWORD=admin123
ENVIRONMENT=development
DEBUG=true
SETUP_TEST_DATA=true
```

### **Option 2: Use sed/echo (Quick Update)**

```bash
cd /Users/mihapro/Development/ecommerce/forecaster_enterprise

# Update JWT_SECRET_KEY (if empty)
sed -i '' 's/^JWT_SECRET_KEY=$/JWT_SECRET_KEY=0ebc0cac6a838232ffc36ed8f5ae7d6b4f2bff520771982a26f7e02a1e90f00f/' .env

# Update NUXT_SESSION_PASSWORD (if empty)
sed -i '' 's/^NUXT_SESSION_PASSWORD=$/NUXT_SESSION_PASSWORD=398a0c4ad0515f8f1874cc97d64ee290a25ca8ec0f6f30ccad438af2a507845e/' .env

# Update for local testing
sed -i '' 's/^ENVIRONMENT=production/ENVIRONMENT=development/' .env
sed -i '' 's/^DEBUG=false/DEBUG=true/' .env
sed -i '' 's/^SETUP_TEST_DATA=false/SETUP_TEST_DATA=true/' .env
sed -i '' 's/^DB_PASSWORD=change-me-in-production/DB_PASSWORD=postgres123/' .env
sed -i '' 's/^ADMIN_PASSWORD=change-me-in-production/ADMIN_PASSWORD=admin123/' .env
```

---

## 🚀 Production Configuration

### **Key Differences:**

| Setting | Local/Testing | Production |
|---------|---------------|------------|
| `ENVIRONMENT` | `development` | `production` |
| `DEBUG` | `true` | `false` |
| `DB_PASSWORD` | Simple (e.g., `postgres123`) | Strong, unique password |
| `ADMIN_PASSWORD` | Simple (e.g., `admin123`) | Strong, unique password |
| `JWT_SECRET_KEY` | Can be in `.env` | **Must be in secret manager** |
| `NUXT_SESSION_PASSWORD` | Can be in `.env` | **Must be in secret manager** |
| `SENTRY_DSN` | Automatically ignored | **Must be in secret manager** |
| Secrets Storage | `.env` file (gitignored) | Secret management service |

### **Production Best Practices:**

1. **Never commit secrets to git**
   - `.env` is in `.gitignore` ✅
   - Use `.env.example` as template ✅

2. **Use Secret Management Services:**
   - **AWS:** AWS Secrets Manager
   - **GCP:** Secret Manager
   - **Azure:** Key Vault
   - **Kubernetes:** Secrets
   - **Docker Swarm:** Docker Secrets

3. **Environment-Specific Values:**
   ```bash
   # Production .env (stored securely, not in git)
   ENVIRONMENT=production
   DEBUG=false
   DB_PASSWORD=<strong-random-password>
   ADMIN_PASSWORD=<strong-random-password>
   JWT_SECRET_KEY=<from-secret-manager>
   NUXT_SESSION_PASSWORD=<from-secret-manager>

   # Error Monitoring (Sentry)
   SENTRY_DSN=<from-secret-manager>
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.2
   SENTRY_PROFILES_SAMPLE_RATE=0.1

   # Frontend Sentry (Nuxt)
   NUXT_PUBLIC_SENTRY_DSN=<from-secret-manager>
   NUXT_PUBLIC_SENTRY_ENVIRONMENT=production
   NUXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1
   ```

4. **Docker Compose with Secrets:**
   ```yaml
   # docker-compose.prod.yml
   services:
     backend:
       environment:
         - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
       secrets:
         - jwt_secret
         - db_password
   
   secrets:
     jwt_secret:
       external: true
     db_password:
       external: true
   ```

5. **CI/CD Pipeline:**
   - Inject secrets as environment variables
   - Never store in code or config files
   - Rotate secrets regularly

---

## 📊 **Sentry Error Monitoring Setup**

### **Why Sentry?**
- **Real-time error tracking** across frontend and backend
- **Performance monitoring** with transaction tracing
- **Multi-tenant error grouping** by client_id
- **Release tracking** and deployment monitoring
- **Automatic alerting** for critical issues

### **Step 1: Create Sentry Projects**

1. **Go to [sentry.io](https://sentry.io)** and create an account
2. **Create two projects:**
   - **Backend Project:** `forecaster-backend` (Python/FastAPI)
   - **Frontend Project:** `forecaster-frontend` (Nuxt.js/Vue)

3. **Note the DSN URLs** for each project:
   - Backend DSN: `https://your-key@sentry.io/project-id`
   - Frontend DSN: `https://your-key@sentry.io/project-id`

### **Step 2: Configure Environment Variables**

#### **Backend Sentry Configuration:**
```bash
# Add to your production environment variables
SENTRY_DSN=https://your-backend-dsn@sentry.io/backend-project-id
SENTRY_ENVIRONMENT=production          # or 'staging'
SENTRY_TRACES_SAMPLE_RATE=0.2          # 20% of requests traced
SENTRY_PROFILES_SAMPLE_RATE=0.1        # 10% of requests profiled
```

#### **Frontend Sentry Configuration:**
```bash
# Add to your production environment variables
NUXT_PUBLIC_SENTRY_DSN=https://your-frontend-dsn@sentry.io/frontend-project-id
NUXT_PUBLIC_SENTRY_ENVIRONMENT=production
NUXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of page loads traced
```

### **Step 3: Deploy and Verify**

#### **Test Backend Sentry:**
```bash
# Trigger a test error in production
curl -X POST https://your-api.com/api/v1/test/sentry-error

# Check Sentry dashboard for the error
# Should appear within 30 seconds
```

#### **Test Frontend Sentry:**
```bash
# Open your production app
# Trigger a JavaScript error (browser console):
throw new Error("Sentry test error")

# Check Sentry dashboard for the error
```

### **Step 4: Configure Alerts**

#### **Critical Error Alerts:**
1. **Go to Sentry Dashboard → Alerts**
2. **Create alert for:**
   - **Error Rate:** >5% error rate in 5 minutes
   - **New Issues:** Alert on first occurrence
   - **Performance:** P95 response time >30 seconds

#### **Business-Specific Alerts:**
1. **Forecast Failures:** Errors in `/api/v1/forecast` endpoint
2. **Database Errors:** SQLAlchemy connection issues
3. **Client-Specific:** High error rates for specific client_ids

### **Step 5: Release Tracking**

#### **Backend Release Tracking:**
```bash
# Set release version in deployment
export GIT_COMMIT_SHA=$(git rev-parse HEAD)
export SENTRY_RELEASE=$GIT_COMMIT_SHA

# Deploy with release info
# Sentry will automatically track which release introduced bugs
```

#### **Frontend Release Tracking:**
```bash
# Nuxt automatically tracks releases via GIT_COMMIT_SHA
# Set in your deployment environment
GIT_COMMIT_SHA=abc123...
```

### **Step 6: Monitor and Tune**

#### **Adjust Sample Rates Based on Usage:**
```bash
# High-traffic production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% sampling

# Lower-traffic staging
SENTRY_TRACES_SAMPLE_RATE=0.5  # 50% sampling

# Development (automatically disabled)
# No Sentry traffic in development
```

#### **Key Metrics to Monitor:**
- **Error Rate:** Should be <1% in production
- **Performance:** P95 API response time <5 seconds
- **Client Distribution:** Errors grouped by client_id
- **Release Health:** Compare error rates across deployments

### **Troubleshooting Sentry**

#### **"Sentry disabled for development environment"**
- ✅ **Expected behavior** - Sentry automatically disabled in development
- ✅ **Solution** - Set `ENVIRONMENT=production` in production

#### **Errors not appearing in Sentry**
```bash
# Check DSN is correct
echo $SENTRY_DSN

# Test with curl
curl -H "X-Sentry-Auth: Sentry sentry_version=7, sentry_key=your-key" \
     https://sentry.io/api/your-project-id/store/
```

#### **High error volume**
- Adjust `SENTRY_TRACES_SAMPLE_RATE` downward
- Add error filtering in Sentry SDK
- Use Sentry's inbound filters

### **Security Considerations**

#### **DSN Exposure:**
- ✅ **Backend DSN:** Private (server-side only)
- ✅ **Frontend DSN:** Public but scoped to project
- ✅ **No sensitive data** sent to Sentry

#### **Data Privacy:**
- ✅ **PII filtering** configured automatically
- ✅ **Business context** (client_id) included for debugging
- ✅ **Stack traces** captured for error resolution

#### **Access Control:**
- ✅ **Team-based access** in Sentry dashboard
- ✅ **Role-based permissions** (admin, developer, viewer)
- ✅ **Audit logs** for Sentry access

---

## **📋 Production Environment Checklist**

### **Required for Production:**
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `JWT_SECRET_KEY` (from secret manager)
- [ ] `NUXT_SESSION_PASSWORD` (from secret manager)
- [ ] `SENTRY_DSN` (from secret manager)
- [ ] `NUXT_PUBLIC_SENTRY_DSN` (from secret manager)

### **Recommended for Production:**
- [ ] `SENTRY_ENVIRONMENT=production`
- [ ] `SENTRY_TRACES_SAMPLE_RATE=0.1-0.2`
- [ ] `GIT_COMMIT_SHA` (for release tracking)
- [ ] Log aggregation setup (ELK/S3/CloudWatch)
- [ ] Monitoring dashboards configured

---

## 🔍 Testing Your Configuration

### **1. Verify .env is Set Up:**

```bash
# Check if required variables are set
grep -E "JWT_SECRET_KEY|NUXT_SESSION_PASSWORD" .env | grep -v "^#"

# Should show:
# JWT_SECRET_KEY=0ebc0cac6a838232ffc36ed8f5ae7d6b4f2bff520771982a26f7e02a1e90f00f
# NUXT_SESSION_PASSWORD=398a0c4ad0515f8f1874cc97d64ee290a25ca8ec0f6f30ccad438af2a507845e
```

### **2. Test Docker Setup:**

```bash
# Start services
docker-compose up -d

# Watch backend logs (should see no errors about missing keys)
docker-compose logs -f backend

# Check health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### **3. Verify Setup Script Ran:**

```bash
# Check if admin user was created
docker-compose exec backend psql -U postgres -d forecaster_enterprise -c "SELECT email, name FROM users;"

# Should show admin@example.com
```

---

## 📋 Environment Variables Checklist

### **Required for Local Testing:**
- [x] `JWT_SECRET_KEY` - Generated secret key
- [x] `NUXT_SESSION_PASSWORD` - Generated secret key
- [x] `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database credentials
- [x] `ADMIN_EMAIL`, `ADMIN_PASSWORD` - Admin user
- [x] `ENVIRONMENT=development` - For local testing
- [x] `DEBUG=true` - For local testing
- [ ] `SENTRY_DSN` - Automatically ignored in development

### **Optional (Have Defaults):**
- [ ] `CLIENT_NAME` - Default: "Demo Client"
- [ ] `CSV_PATH` - Default: uses synthetic data
- [ ] `TEST_EMAIL`, `TEST_PASSWORD` - Optional test user
- [ ] `LICENSE_URL`, `LICENSE_KEY` - Only if using license system

---

## 🛠️ Troubleshooting

### **"JWT_SECRET_KEY must be set" Error:**
```bash
# Generate and add to .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### **"NUXT_SESSION_PASSWORD not set" Error:**
```bash
# Generate and add to .env
echo "NUXT_SESSION_PASSWORD=$(openssl rand -hex 32)" >> .env
```

### **Database Connection Issues:**
- Verify `DB_USER`, `DB_PASSWORD`, `DB_NAME` match docker-compose.yml
- Check database container is running: `docker-compose ps db`

---

## 📚 Summary

**For Local Testing:**
1. ✅ Set `JWT_SECRET_KEY` and `NUXT_SESSION_PASSWORD` (generated keys provided above)
2. ✅ Use simple passwords (`postgres123`, `admin123`)
3. ✅ Set `ENVIRONMENT=development` and `DEBUG=true`
4. ✅ Enable `SETUP_TEST_DATA=true` for demo data

**For Production:**
1. ✅ Use strong, unique passwords
2. ✅ Store secrets in secret management service
3. ✅ Set `ENVIRONMENT=production` and `DEBUG=false`
4. ✅ Configure Sentry error monitoring (see Sentry section above)
5. ✅ Never commit secrets to version control
6. ✅ Rotate secrets regularly
