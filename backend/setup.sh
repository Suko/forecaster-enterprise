#!/bin/bash
# First-time setup script for backend
# This script sets up the database, creates an admin user, and prepares test data
# 
# Usage: ./setup.sh
# 
# This script will:
# - Check prerequisites (uv, Python, PostgreSQL)
# - Create .env file if missing
# - Install dependencies
# - Run database migrations
# - Create admin and test users
# - Import sales data (CSV or M5)
# - Set up test data (products, locations, stock)
# - Shift dates to recent
# - Populate historical stock
#
# Just run it and it does everything!

# Don't use set -e here - we want to handle errors gracefully
# set -e  # Exit on error

# Set PYTHONPATH to include backend directory (required for Docker/container environments)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$SCRIPT_DIR"

# Detect Docker environment - if in Docker, use python/alembic directly (venv is active)
if [ -f "/.dockerenv" ] || [ -n "$DOCKER_CONTAINER" ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_DOCKER=true
    RUN_PREFIX=""
else
    IN_DOCKER=false
    RUN_PREFIX="uv run "
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  Backend First-Time Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "This script will set up everything automatically."
echo "Just sit back and let it do the work! 🚀"
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
USE_M5_DATA="${USE_M5_DATA:-false}"

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
        --use-m5-data)
            USE_M5_DATA="true"
            M5_ONLY="true"
            shift
            ;;
        --csv-only)
            CSV_ONLY="true"
            shift
            ;;
        --m5-only)
            M5_ONLY="true"
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
            echo "  --use-m5-data             Import M5 dataset (deprecated: use --m5-only)"
            echo "  --csv-only                Import only CSV data (skip M5)"
            echo "  --m5-only                 Import only M5 data (skip CSV)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Default behavior: Imports both CSV and M5 datasets"
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

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================
echo -e "${GREEN}[0/7]${NC} Checking prerequisites..."
echo ""

# Check for uv (only needed outside Docker)
if [ "$IN_DOCKER" = true ]; then
    echo -e "${GREEN}✓${NC} Running in Docker (venv already active)"
elif ! command -v uv &> /dev/null; then
    echo -e "${RED}✗${NC} uv is not installed"
    echo "   Install from: https://github.com/astral-sh/uv"
    echo "   Or run: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
else
    echo -e "${GREEN}✓${NC} uv found"
fi

# Check for Python 3.12+
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [ -z "$PYTHON_VERSION" ]; then
    echo -e "${YELLOW}⚠${NC} Python3 not found (uv will handle this)"
else
    echo -e "${GREEN}✓${NC} Python found: $(python3 --version)"
fi

# Check PostgreSQL connection (optional - will fail later if not available)
echo -e "${GREEN}✓${NC} Prerequisites check complete"
echo ""

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
echo -e "${GREEN}[0.5/7]${NC} Setting up environment..."

# Skip .env creation in Docker (environment variables are set by docker-compose)
if [ "$IN_DOCKER" = true ]; then
    echo -e "${GREEN}✓${NC} Using environment variables from Docker"
else
    # Create .env from .env.example if it doesn't exist
    ENV_FILE="$SCRIPT_DIR/.env"
    ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            echo "  Creating .env file from .env.example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            
            # Generate a secure JWT secret key
            if command -v openssl &> /dev/null; then
                JWT_SECRET=$(openssl rand -hex 32)
                # Replace JWT_SECRET_KEY in .env (works on both macOS and Linux)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE"
                else
                    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE"
                fi
                echo -e "${GREEN}✓${NC} Generated secure JWT secret key"
            else
                echo -e "${YELLOW}⚠${NC} openssl not found - using default JWT secret (change in production!)"
            fi
            
            echo -e "${GREEN}✓${NC} Created .env file"
            echo -e "${YELLOW}⚠${NC} Please check DATABASE_URL in .env matches your PostgreSQL setup"
        else
            echo -e "${YELLOW}⚠${NC} .env.example not found - using environment variables"
        fi
    else
        echo -e "${GREEN}✓${NC} .env file already exists"
    fi
fi
echo ""

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================
echo -e "${GREEN}[0.7/7]${NC} Installing dependencies..."
if [ "$IN_DOCKER" = true ]; then
    echo -e "${GREEN}✓${NC} Dependencies already installed in Docker image"
else
    echo "  This may take a few minutes on first run..."
    if uv sync --quiet 2>&1 | grep -v "Resolved\|Downloaded\|Installed"; then
        echo -e "${GREEN}✓${NC} Dependencies installed"
    else
        echo -e "${GREEN}✓${NC} Dependencies ready"
    fi
fi
echo ""

# ============================================================================
# DATABASE CONNECTION CHECK
# ============================================================================
echo -e "${GREEN}[0.9/7]${NC} Checking database connection..."
# Try to connect to database (non-blocking - will fail gracefully in migrations if needed)
if ${RUN_PREFIX}python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
try:
    from models.database import get_async_session_local
    from sqlalchemy import text
    import asyncio
    async def check():
        async with get_async_session_local()() as session:
            await session.execute(text('SELECT 1'))
    asyncio.run(check())
    print('✓ Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'⚠ Database connection failed: {e}')
    print('   Make sure PostgreSQL is running and DATABASE_URL is correct')
    sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Database is ready"
else
    echo -e "${YELLOW}⚠${NC} Could not connect to database"
    echo "   Make sure PostgreSQL is running:"
    echo "   - macOS: brew services start postgresql"
    echo "   - Linux: sudo systemctl start postgresql"
    echo "   - Or check DATABASE_URL in .env file"
    echo ""
    echo "   Continuing anyway - migrations will fail if database is not available..."
fi
echo ""

# ============================================================================
# MAIN SETUP STEPS
# ============================================================================

# Step 1: Run migrations
echo -e "${GREEN}[1/7]${NC} Running database migrations..."
${RUN_PREFIX}alembic upgrade head
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Migrations completed"
else
    echo -e "${RED}✗${NC} Migration failed"
    exit 1
fi
echo ""

# Step 1.5: Create client first (required for users)
echo -e "${GREEN}[1.5/7]${NC} Creating demo client..."
CLIENT_OUTPUT=$(${RUN_PREFIX}python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from models.database import get_async_session_local
from models.client import Client
from sqlalchemy import select

async def create_client():
    name = '$CLIENT_NAME'
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Client).where(Client.name == name))
        existing = result.scalar_one_or_none()
        if existing:
            print(f'Client already exists: {existing.client_id}')
            return str(existing.client_id)
        client = Client(name=name, timezone='UTC', currency='EUR', is_active=True)
        session.add(client)
        await session.commit()
        await session.refresh(client)
        print(f'Created client: {client.client_id}')
        return str(client.client_id)

print(asyncio.run(create_client()))
" 2>&1)
echo "$CLIENT_OUTPUT"
CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | tail -1)
if [ -n "$CLIENT_ID" ]; then
    echo -e "${GREEN}✓${NC} Client ready: $CLIENT_ID"
    export CLIENT_ID
else
    echo -e "${YELLOW}⚠${NC} Could not extract client ID"
fi
echo ""

# Step 2: Create admin user
if [ "$SKIP_ADMIN" != "true" ]; then
    echo -e "${GREEN}[2/7]${NC} Creating admin user..."
    echo "  Email: $ADMIN_EMAIL"
    echo "  Name: $ADMIN_NAME"
    
    if [ -n "$CLIENT_ID" ]; then
        ${RUN_PREFIX}python create_user.py "$ADMIN_EMAIL" "$ADMIN_PASSWORD" \
            --name "$ADMIN_NAME" \
            --admin \
            --client-id "$CLIENT_ID"
    else
        ${RUN_PREFIX}python create_user.py "$ADMIN_EMAIL" "$ADMIN_PASSWORD" \
            --name "$ADMIN_NAME" \
            --admin
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Admin user created"
    else
        echo -e "${YELLOW}⚠${NC} Admin user creation failed (may already exist)"
    fi
else
    echo -e "${YELLOW}[2/7]${NC} Skipping admin user creation (--skip-admin)"
fi
echo ""

# Step 3: Create test user
if [ "$SKIP_TEST_USER" != "true" ]; then
    echo -e "${GREEN}[3/7]${NC} Creating test user..."
    echo "  Email: $TEST_EMAIL"
    echo "  Name: $TEST_NAME"
    
    if [ -n "$CLIENT_ID" ]; then
        ${RUN_PREFIX}python create_user.py "$TEST_EMAIL" "$TEST_PASSWORD" \
            --name "$TEST_NAME" \
            --client-id "$CLIENT_ID"
    else
        ${RUN_PREFIX}python create_user.py "$TEST_EMAIL" "$TEST_PASSWORD" \
            --name "$TEST_NAME"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Test user created"
    else
        echo -e "${YELLOW}⚠${NC} Test user creation failed (may already exist)"
    fi
else
    echo -e "${YELLOW}[3/7]${NC} Skipping test user creation (--skip-test-user)"
fi
echo ""

# Step 4: Import sales data (required for test data setup)
# This imports sales data into ts_demand_daily table
# The sales data will be shifted to recent dates in Step 5
# Default: Import both CSV and M5 datasets
if [ "$SKIP_CSV_IMPORT" != "true" ]; then
    # Determine what to import
    IMPORT_CSV="false"
    IMPORT_M5="false"
    
    if [ "$M5_ONLY" == "true" ]; then
        # Only M5
        IMPORT_M5="true"
    elif [ "$CSV_ONLY" == "true" ]; then
        # Only CSV
        IMPORT_CSV="true"
    else
        # Default: Both CSV and M5
        IMPORT_CSV="true"
        IMPORT_M5="true"
    fi
    
    # Import CSV if needed
    if [ "$IMPORT_CSV" == "true" ]; then
        echo -e "${GREEN}[4/7]${NC} Importing CSV sales data..."
        
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
                    echo -e "${YELLOW}⚠${NC} CSV file not found: $CSV_PATH"
                    echo "   Tried: $CSV_PATH"
                    echo "   Tried: $BACKEND_DIR/$CSV_PATH"
                    echo "   Tried: $PROJECT_ROOT/$CSV_PATH"
                    if [ "$IN_DOCKER" = true ]; then
                        echo "   (This is expected in Docker - data files are not mounted)"
                        IMPORT_CSV="false"
                    else
                        exit 1
                    fi
                fi
            fi
        fi
        
        # Only import if file was found
        if [ "$IMPORT_CSV" == "true" ] && [ -f "$CSV_PATH" ]; then
            echo "  CSV path: $CSV_PATH"
            
            # Create or get the client and import CSV
            CLIENT_OUTPUT=$(${RUN_PREFIX}python scripts/setup_demo_client.py --name "$CLIENT_NAME" --csv "$CSV_PATH" 2>&1)
            echo "$CLIENT_OUTPUT"
            
            # Extract client ID from CSV import output
            CSV_CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -i "Client ID:" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
            
            if [ -z "$CSV_CLIENT_ID" ]; then
                CSV_CLIENT_ID=$(echo "$CLIENT_OUTPUT" | grep -E "(Client.*ID|client_id)" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
            fi
            
            if [ -n "$CSV_CLIENT_ID" ]; then
                echo -e "${GREEN}✓${NC} CSV data imported"
                echo "  Client ID: $CSV_CLIENT_ID"
                export CLIENT_ID="$CSV_CLIENT_ID"
            fi
        fi
    fi
    
    # Import M5 if needed (skip in Docker by default - takes too long for first start)
    if [ "$IMPORT_M5" == "true" ]; then
        if [ "$IN_DOCKER" = true ]; then
            echo -e "${YELLOW}[4/7]${NC} Skipping M5 dataset download in Docker (too slow for first start)"
            echo "   You can import data later using the API or mounted volumes"
            IMPORT_M5="false"
        else
            echo -e "${GREEN}[4/7]${NC} Downloading and importing M5 dataset..."
            echo "  This will download M5 dataset from Zenodo (if not already downloaded)"
            echo "  Then import selected SKUs to ts_demand_daily"
            echo "  Note: No API credentials needed - downloads directly from Zenodo"
            
            # Download and import M5 data (use existing client if CSV was imported)
            if [ -n "$CLIENT_ID" ]; then
                M5_OUTPUT=$(${RUN_PREFIX}python scripts/download_m5_data.py --client-id "$CLIENT_ID" --n-skus 40 2>&1)
            else
                M5_OUTPUT=$(${RUN_PREFIX}python scripts/download_m5_data.py --client-name "$CLIENT_NAME" --n-skus 40 2>&1)
            fi
            echo "$M5_OUTPUT"
            
            # Extract client ID from M5 import output (if not already set)
            if [ -z "$CLIENT_ID" ]; then
                CLIENT_ID=$(echo "$M5_OUTPUT" | grep -i "Client ID:" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
                
                if [ -z "$CLIENT_ID" ]; then
                    CLIENT_ID=$(echo "$M5_OUTPUT" | grep -E "(Client.*ID|client_id)" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
                fi
                
                if [ -n "$CLIENT_ID" ]; then
                    echo -e "${GREEN}✓${NC} M5 data imported"
                    echo "  Client ID: $CLIENT_ID"
                    export CLIENT_ID="$CLIENT_ID"
                fi
            else
                echo -e "${GREEN}✓${NC} M5 data imported (using existing client)"
            fi
        fi
    fi
    
    # Final fallback: Try to get client ID from database if still not set
    if [ -z "$CLIENT_ID" ]; then
        echo -e "${YELLOW}⚠${NC} Could not extract client ID from import output"
        echo "  Attempting to get client ID from database..."
        CLIENT_ID=$(${RUN_PREFIX}python -c "
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
        else
            if [ "$IN_DOCKER" = true ]; then
                echo -e "${YELLOW}⚠${NC} No data imported in Docker - client and users created, but no demo data"
                echo "   Import data using the API or mount CSV files to /data volume"
            else
                echo -e "${RED}✗${NC} Could not determine client ID. Please check the import output above."
                exit 1
            fi
        fi
    fi
else
    echo -e "${YELLOW}[4/7]${NC} Skipping CSV import (--skip-csv-import)"
    # Try to get existing client ID
    CLIENT_ID=$(${RUN_PREFIX}python -c "
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
    
    # Assign client to admin and test users (if they don't have one)
    if [ -n "$CLIENT_ID" ]; then
        echo -e "${GREEN}[4.5/7]${NC} Assigning client to users..."
        ${RUN_PREFIX}python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from models.database import get_async_session_local
from models.user import User
from models.client import Client
from sqlalchemy import select
import uuid

async def assign_client_to_users():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Get client
        result = await session.execute(
            select(Client).where(Client.client_id == uuid.UUID('$CLIENT_ID'))
        )
        client = result.scalar_one_or_none()
        if not client:
            return
        
        # Assign to admin user
        result = await session.execute(
            select(User).where(User.email == '$ADMIN_EMAIL')
        )
        admin = result.scalar_one_or_none()
        if admin and not admin.client_id:
            admin.client_id = client.client_id
            print('  ✓ Assigned client to admin user')
        
        # Assign to test user
        result = await session.execute(
            select(User).where(User.email == '$TEST_EMAIL')
        )
        test_user = result.scalar_one_or_none()
        if test_user and not test_user.client_id:
            test_user.client_id = client.client_id
            print('  ✓ Assigned client to test user')
        
        await session.commit()

asyncio.run(assign_client_to_users())
" 2>/dev/null || true
    fi
fi
echo ""

# Step 5: Set up test data (products, locations, suppliers, stock levels)
# This also shifts sales data dates to recent and populates historical stock
# In Docker without data import, skip this step
if [ "$SKIP_TEST_DATA" != "true" ]; then
    # Check if we should skip in Docker (no data imported)
    if [ "$IN_DOCKER" = true ] && [ "$IMPORT_CSV" != "true" ] && [ "$IMPORT_M5" != "true" ]; then
        echo -e "${YELLOW}[5/7]${NC} Skipping test data setup (no sales data imported in Docker)"
        echo "   To set up test data, mount your CSV files and run setup manually"
    else
        echo -e "${GREEN}[5/7]${NC} Setting up test data (products, locations, suppliers, stock)..."
        echo "  Client name: $CLIENT_NAME"
        echo "  This will also:"
        echo "    - Shift sales data dates to recent (makes all data relative to today)"
        echo "    - Populate historical stock data (stock_on_date)"
        
        if [ -n "$CLIENT_ID" ]; then
            CLIENT_ARG="--client-id $CLIENT_ID"
        else
            CLIENT_ARG="--client-name $CLIENT_NAME"
        fi
        
        # Run setup_test_data.py and capture output
        # This automatically:
        # - Creates products, locations, suppliers, stock levels
        # - Shifts sales data dates to recent (Step 9)
        # - Populates historical stock (Step 10)
        TEST_DATA_OUTPUT=$(${RUN_PREFIX}python scripts/setup_test_data.py $CLIENT_ARG 2>&1)
        echo "$TEST_DATA_OUTPUT"
        
        if echo "$TEST_DATA_OUTPUT" | grep -qi "error\|failed\|warning.*no.*item_ids"; then
            echo -e "${YELLOW}⚠${NC} Test data setup had issues - check output above"
        else
            echo -e "${GREEN}✓${NC} Test data setup completed"
            echo -e "${GREEN}✓${NC} Sales data dates shifted to recent"
            echo -e "${GREEN}✓${NC} Historical stock data populated"
        fi
    fi
else
    echo -e "${YELLOW}[5/7]${NC} Skipping test data setup (--skip-test-data)"
fi
echo ""

# Step 6: Verify setup
echo -e "${GREEN}[6/7]${NC} Verifying setup..."
# Quick verification that data exists
if [ -n "$CLIENT_ID" ] && [ "$SKIP_TEST_DATA" != "true" ]; then
    VERIFY_OUTPUT=$(${RUN_PREFIX}python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from models.database import get_async_session_local
from models.product import Product
from sqlalchemy import select, func

async def verify():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Product.product_id)))
        count = result.scalar()
        print(f'Products: {count}')
asyncio.run(verify())
" 2>/dev/null)
    if echo "$VERIFY_OUTPUT" | grep -q "Products: [1-9]"; then
        echo -e "${GREEN}✓${NC} Test data verified"
    else
        echo -e "${YELLOW}⚠${NC} Verification incomplete - check logs above"
    fi
fi
echo ""

# Step 7: Summary
echo -e "${GREEN}[7/7]${NC} Setup complete! 🎉"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🎉 Setup Complete! You're ready to go!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Quick Start:"
echo ""
echo "1. Start the server:"
echo "   ${GREEN}cd $SCRIPT_DIR${NC}"
echo "   ${GREEN}${RUN_PREFIX}uvicorn main:app --reload${NC}"
echo ""
echo "2. Access the API:"
echo "   ${GREEN}http://localhost:8000${NC}"
echo "   ${GREEN}http://localhost:8000/docs${NC} (API documentation)"
echo ""
echo "3. Login credentials:"
echo "   ${YELLOW}Admin User:${NC}"
echo "     Email: ${GREEN}$ADMIN_EMAIL${NC}"
echo "     Password: ${GREEN}$ADMIN_PASSWORD${NC}"
echo ""
echo "   ${YELLOW}Test User:${NC}"
echo "     Email: ${GREEN}$TEST_EMAIL${NC}"
echo "     Password: ${GREEN}$TEST_PASSWORD${NC}"
echo ""
if [ -n "$CLIENT_ID" ]; then
    echo "4. Client ID: ${GREEN}$CLIENT_ID${NC}"
    echo ""
fi
echo "5. Run tests:"
echo "   ${GREEN}${RUN_PREFIX}pytest tests/test_api/test_inventory_api.py -v${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 Tip: If you need to reset test data, run:"
echo "   ${GREEN}${RUN_PREFIX}python scripts/reset_test_data.py --client-id $CLIENT_ID${NC}"
echo ""

