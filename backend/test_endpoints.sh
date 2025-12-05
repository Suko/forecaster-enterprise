#!/bin/bash
# Test script for Phase 1.6 - Auth Endpoints

BASE_URL="http://localhost:8000"

echo "🧪 Testing Forecaster Enterprise API Endpoints"
echo "=============================================="
echo ""

# Test 1: Health endpoint
echo "1️⃣  Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "   ✅ Health check passed: $HEALTH_RESPONSE"
else
    echo "   ❌ Health check failed: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo "2️⃣  Testing root endpoint..."
ROOT_RESPONSE=$(curl -s "$BASE_URL/")
if [[ $ROOT_RESPONSE == *"Forecaster Enterprise"* ]]; then
    echo "   ✅ Root endpoint passed: $ROOT_RESPONSE"
else
    echo "   ❌ Root endpoint failed: $ROOT_RESPONSE"
fi
echo ""

# Test 3: Register user
echo "3️⃣  Testing /auth/register endpoint..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }')

if [[ $REGISTER_RESPONSE == *"email"* ]] || [[ $REGISTER_RESPONSE == *"already registered"* ]]; then
    echo "   ✅ Registration endpoint responded: $REGISTER_RESPONSE"
else
    echo "   ⚠️  Registration response: $REGISTER_RESPONSE"
fi
echo ""

# Test 4: Login
echo "4️⃣  Testing /auth/login endpoint..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123")

if [[ $LOGIN_RESPONSE == *"access_token"* ]]; then
    echo "   ✅ Login successful!"
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${TOKEN:0:50}..."
    echo ""
    
    # Test 5: Protected endpoint
    echo "5️⃣  Testing /auth/me (protected endpoint)..."
    ME_RESPONSE=$(curl -s "$BASE_URL/auth/me" \
      -H "Authorization: Bearer $TOKEN")
    
    if [[ $ME_RESPONSE == *"email"* ]]; then
        echo "   ✅ Protected endpoint works: $ME_RESPONSE"
    else
        echo "   ❌ Protected endpoint failed: $ME_RESPONSE"
    fi
else
    echo "   ❌ Login failed: $LOGIN_RESPONSE"
    echo "   (Make sure user exists - try registration first)"
fi
echo ""

echo "=============================================="
echo "✅ Testing complete!"
echo ""
echo "Next steps:"
echo "1. Create database: createdb forecaster_enterprise"
echo "2. Run migrations: alembic upgrade head"
echo "3. Start server: uvicorn main:app --reload"
echo "4. Run this test script again"

