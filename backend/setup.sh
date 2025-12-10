#!/bin/bash
# First-time setup script for backend
# This script sets up the database, creates an admin user, and prepares test data

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "  Backend First-Time Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
ADMIN_NAME="${ADMIN_NAME:-Admin User}"
CLIENT_NAME="${CLIENT_NAME:-Demo Client}"
SKIP_ADMIN="${SKIP_ADMIN:-false}"
SKIP_TEST_DATA="${SKIP_TEST_DATA:-false}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --admin-email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        --admin-password)
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --admin-name)
            ADMIN_NAME="$2"
            shift 2
            ;;
        --client-name)
            CLIENT_NAME="$2"
            shift 2
            ;;
        --skip-admin)
            SKIP_ADMIN="true"
            shift
            ;;
        --skip-test-data)
            SKIP_TEST_DATA="true"
            shift
            ;;
        --help)
            echo "Usage: ./setup.sh [options]"
            echo ""
            echo "Options:"
            echo "  --admin-email EMAIL       Admin user email (default: admin@example.com)"
            echo "  --admin-password PWD      Admin user password (default: admin123)"
            echo "  --admin-name NAME         Admin user name (default: Admin User)"
            echo "  --client-name NAME        Client name (default: Demo Client)"
            echo "  --skip-admin              Skip admin user creation"
            echo "  --skip-test-data          Skip test data setup"
            echo "  --help                    Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME, CLIENT_NAME"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Step 1: Run migrations
echo -e "${GREEN}[1/4]${NC} Running database migrations..."
uv run alembic upgrade head
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Migrations completed"
else
    echo -e "${RED}✗${NC} Migration failed"
    exit 1
fi
echo ""

# Step 2: Create admin user
if [ "$SKIP_ADMIN" != "true" ]; then
    echo -e "${GREEN}[2/4]${NC} Creating admin user..."
    echo "  Email: $ADMIN_EMAIL"
    echo "  Name: $ADMIN_NAME"
    
    uv run python create_user.py "$ADMIN_EMAIL" "$ADMIN_PASSWORD" \
        --name "$ADMIN_NAME" \
        --admin
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Admin user created"
    else
        echo -e "${YELLOW}⚠${NC} Admin user creation failed (may already exist)"
    fi
else
    echo -e "${YELLOW}[2/4]${NC} Skipping admin user creation (--skip-admin)"
fi
echo ""

# Step 3: Set up test data
if [ "$SKIP_TEST_DATA" != "true" ]; then
    echo -e "${GREEN}[3/4]${NC} Setting up test data..."
    echo "  Client name: $CLIENT_NAME"
    
    # Run setup_test_data.py and capture output
    CLIENT_OUTPUT=$(uv run python scripts/setup_test_data.py --client-name "$CLIENT_NAME" 2>&1)
    echo "$CLIENT_OUTPUT"
    
    # Extract client ID from output (look for "Client ID: <uuid>" pattern)
    CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -i "Client ID:" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    
    # If not found, try to extract from "Using existing client" or "Created new client" lines
    if [ -z "$CLIENT_ID" ]; then
        CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -E "(Using existing client|Created new client)" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    fi
    
    if [ -n "$CLIENT_ID" ]; then
        echo -e "${GREEN}✓${NC} Test data setup completed"
        echo "  Client ID: $CLIENT_ID"
        export CLIENT_ID="$CLIENT_ID"
    else
        echo -e "${YELLOW}⚠${NC} Test data setup completed (could not extract client ID)"
        echo "  Check the output above for the client ID"
    fi
else
    echo -e "${YELLOW}[3/4]${NC} Skipping test data setup (--skip-test-data)"
fi
echo ""

# Step 4: Summary
echo -e "${GREEN}[4/4]${NC} Setup complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Start the server:"
echo "   ${GREEN}uv run uvicorn main:app --reload${NC}"
echo ""
echo "2. Login with admin credentials:"
echo "   Email: ${YELLOW}$ADMIN_EMAIL${NC}"
echo "   Password: ${YELLOW}$ADMIN_PASSWORD${NC}"
echo ""
echo "3. Run tests:"
echo "   ${GREEN}uv run pytest tests/test_api/test_inventory_api.py -v${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"

