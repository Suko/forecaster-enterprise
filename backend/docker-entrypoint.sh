#!/bin/bash
set -e

echo "Starting Forecaster Enterprise Backend..."

# Wait for database to be ready
echo "Waiting for database..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# First-time setup flag (check if users table has any records)
FIRST_TIME_SETUP=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT CASE WHEN EXISTS (SELECT 1 FROM users) THEN 'false' ELSE 'true' END;" 2>/dev/null || echo "true")

if [ "$FIRST_TIME_SETUP" = "true" ]; then
  echo "First-time setup detected..."
  
  # Create admin user
  if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "Creating admin user..."
    python create_user.py "$ADMIN_EMAIL" "$ADMIN_PASSWORD" \
      --name "${ADMIN_NAME:-Admin User}" \
      --admin || echo "Admin user may already exist"
  fi
  
  # Setup test data if requested
  if [ "$SETUP_TEST_DATA" = "true" ]; then
    echo "Setting up test data..."
    python scripts/setup_test_data.py --client-name "${CLIENT_NAME:-Demo Client}" || echo "Test data setup skipped"
  fi
  
  echo "First-time setup completed!"
else
  echo "Existing database detected, skipping first-time setup"
fi

# Start the application
echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
