#!/bin/bash
# First-time setup script for backend
# This script sets up the database, creates an admin user, and prepares test data

# Don't use set -e here - we want to handle errors gracefully
# set -e  # Exit on error

# Set PYTHONPATH to include backend directory (required for Docker/container environments)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$SCRIPT_DIR"

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
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-testpassword123}"
TEST_NAME="${TEST_NAME:-Test User}"
CLIENT_NAME="${CLIENT_NAME:-Demo Client}"
CSV_PATH="${CSV_PATH:-../data/synthetic_data/synthetic_ecom_chronos2_demo.csv}"
SKIP_ADMIN="${SKIP_ADMIN:-false}"
SKIP_TEST_USER="${SKIP_TEST_USER:-false}"
SKIP_TEST_DATA="${SKIP_TEST_DATA:-false}"
SKIP_CSV_IMPORT="${SKIP_CSV_IMPORT:-false}"

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
        --skip-test-user)
            SKIP_TEST_USER="true"
            shift
            ;;
        --skip-csv-import)
            SKIP_CSV_IMPORT="true"
            shift
            ;;
        --csv-path)
            CSV_PATH="$2"
            shift 2
            ;;
        --test-email)
            TEST_EMAIL="$2"
            shift 2
            ;;
        --test-password)
            TEST_PASSWORD="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./setup.sh [options]"
            echo ""
            echo "Options:"
            echo "  --admin-email EMAIL       Admin user email (default: admin@example.com)"
            echo "  --admin-password PWD      Admin user password (default: admin123)"
            echo "  --admin-name NAME         Admin user name (default: Admin User)"
            echo "  --client-name NAME        Client name (default: Demo Client)"
            echo "  --test-email EMAIL        Test user email (default: test@example.com)"
            echo "  --test-password PWD        Test user password (default: testpassword123)"
            echo "  --csv-path PATH           Path to CSV file (default: ../data/synthetic_data/synthetic_ecom_chronos2_demo.csv)"
            echo "  --skip-admin              Skip admin user creation"
            echo "  --skip-test-user          Skip test user creation"
            echo "  --skip-csv-import         Skip CSV data import"
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
echo -e "${GREEN}[1/6]${NC} Running database migrations..."
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
    echo -e "${GREEN}[2/6]${NC} Creating admin user..."
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
    echo -e "${YELLOW}[2/6]${NC} Skipping admin user creation (--skip-admin)"
fi
echo ""

# Step 3: Create test user
if [ "$SKIP_TEST_USER" != "true" ]; then
    echo -e "${GREEN}[3/6]${NC} Creating test user..."
    echo "  Email: $TEST_EMAIL"
    echo "  Name: $TEST_NAME"
    
    uv run python create_user.py "$TEST_EMAIL" "$TEST_PASSWORD" \
        --name "$TEST_NAME"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Test user created"
    else
        echo -e "${YELLOW}⚠${NC} Test user creation failed (may already exist)"
    fi
else
    echo -e "${YELLOW}[3/6]${NC} Skipping test user creation (--skip-test-user)"
fi
echo ""

# Step 4: Import CSV data (required for test data setup)
if [ "$SKIP_CSV_IMPORT" != "true" ]; then
    echo -e "${GREEN}[4/6]${NC} Importing CSV data..."
    
    # Resolve CSV path (relative to backend directory or absolute)
    if [ ! -f "$CSV_PATH" ]; then
        # Try relative to backend directory
        BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
        CSV_ABS_PATH="$BACKEND_DIR/$CSV_PATH"
        if [ -f "$CSV_ABS_PATH" ]; then
            CSV_PATH="$CSV_ABS_PATH"
        else
            # Try relative to project root
            PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"
            CSV_ABS_PATH="$PROJECT_ROOT/$CSV_PATH"
            if [ -f "$CSV_ABS_PATH" ]; then
                CSV_PATH="$CSV_ABS_PATH"
            else
                echo -e "${RED}✗${NC} CSV file not found: $CSV_PATH"
                echo "   Tried: $CSV_PATH"
                echo "   Tried: $BACKEND_DIR/$CSV_PATH"
                echo "   Tried: $PROJECT_ROOT/$CSV_PATH"
                exit 1
            fi
        fi
    fi
    
    echo "  CSV path: $CSV_PATH"
    
    # First, create or get the client and import CSV
    CLIENT_OUTPUT=$(uv run python scripts/setup_demo_client.py --name "$CLIENT_NAME" --csv "$CSV_PATH" 2>&1)
    echo "$CLIENT_OUTPUT"
    
    # Extract client ID from output
    CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -i "Client ID:" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    
    if [ -z "$CLIENT_ID" ]; then
        CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -E "(Client.*ID|client_id)" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    fi
    
    if [ -n "$CLIENT_ID" ]; then
        echo -e "${GREEN}✓${NC} CSV data imported"
        echo "  Client ID: $CLIENT_ID"
        export CLIENT_ID="$CLIENT_ID"
    else
        echo -e "${YELLOW}⚠${NC} CSV import completed (could not extract client ID)"
        echo "  Check the output above for the client ID"
        # Try to get client ID from database
        CLIENT_ID=$(uv run python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from models.database import get_async_session_local
from models.client import Client
from sqlalchemy import select

async def get_client():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Client).where(Client.name == '$CLIENT_NAME'))
        client = result.scalar_one_or_none()
        if client:
            print(str(client.client_id))
asyncio.run(get_client())
" 2>/dev/null)
        if [ -n "$CLIENT_ID" ]; then
            echo "  Found Client ID: $CLIENT_ID"
            export CLIENT_ID="$CLIENT_ID"
        fi
    fi
else
    echo -e "${YELLOW}[4/6]${NC} Skipping CSV import (--skip-csv-import)"
    # Try to get existing client ID
    CLIENT_ID=$(uv run python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from models.database import get_async_session_local
from models.client import Client
from sqlalchemy import select

async def get_client():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Client).where(Client.name == '$CLIENT_NAME'))
        client = result.scalar_one_or_none()
        if client:
            print(str(client.client_id))
asyncio.run(get_client())
" 2>/dev/null)
    if [ -n "$CLIENT_ID" ]; then
        echo "  Using existing Client ID: $CLIENT_ID"
        export CLIENT_ID="$CLIENT_ID"
    fi
fi
echo ""

# Step 5: Set up test data (products, locations, suppliers, stock levels)
if [ "$SKIP_TEST_DATA" != "true" ]; then
    echo -e "${GREEN}[5/6]${NC} Setting up test data (products, locations, suppliers, stock)..."
    echo "  Client name: $CLIENT_NAME"
    
    if [ -n "$CLIENT_ID" ]; then
        CLIENT_ARG="--client-id $CLIENT_ID"
    else
        CLIENT_ARG="--client-name $CLIENT_NAME"
    fi
    
    # Run setup_test_data.py and capture output
    TEST_DATA_OUTPUT=$(uv run python scripts/setup_test_data.py $CLIENT_ARG 2>&1)
    echo "$TEST_DATA_OUTPUT"
    
    if echo "$TEST_DATA_OUTPUT" | grep -qi "error\|failed\|warning.*no.*item_ids"; then
        echo -e "${YELLOW}⚠${NC} Test data setup had issues - check output above"
    else
        echo -e "${GREEN}✓${NC} Test data setup completed"
    fi
else
    echo -e "${YELLOW}[5/6]${NC} Skipping test data setup (--skip-test-data)"
fi
echo ""

# Step 6: Summary
echo -e "${GREEN}[6/6]${NC} Setup complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Start the server:"
echo "   ${GREEN}uv run uvicorn main:app --reload${NC}"
echo ""
echo "2. Login credentials:"
echo "   Admin:"
echo "     Email: ${YELLOW}$ADMIN_EMAIL${NC}"
echo "     Password: ${YELLOW}$ADMIN_PASSWORD${NC}"
echo "   Test User:"
echo "     Email: ${YELLOW}$TEST_EMAIL${NC}"
echo "     Password: ${YELLOW}$TEST_PASSWORD${NC}"
if [ -n "$CLIENT_ID" ]; then
    echo ""
    echo "3. Client ID: ${YELLOW}$CLIENT_ID${NC}"
fi
echo ""
echo "4. Run tests:"
echo "   ${GREEN}uv run pytest tests/test_api/test_inventory_api.py -v${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"

