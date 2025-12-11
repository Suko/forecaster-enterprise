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

# Always run migrations first
echo "Running database migrations..."
alembic upgrade head

# First-time setup flag (check if users table has any records)
FIRST_TIME_SETUP=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT CASE WHEN EXISTS (SELECT 1 FROM users) THEN 'false' ELSE 'true' END;" 2>/dev/null || echo "true")

if [ "$FIRST_TIME_SETUP" = "true" ]; then
  echo "First-time setup detected, running setup.sh..."
  
  # Build arguments array for setup.sh (properly handles spaces in values)
  SETUP_ARGS=()
  [ -n "$ADMIN_EMAIL" ] && SETUP_ARGS+=("--admin-email" "$ADMIN_EMAIL")
  [ -n "$ADMIN_PASSWORD" ] && SETUP_ARGS+=("--admin-password" "$ADMIN_PASSWORD")
  [ -n "$ADMIN_NAME" ] && SETUP_ARGS+=("--admin-name" "$ADMIN_NAME")
  [ -n "$CLIENT_NAME" ] && SETUP_ARGS+=("--client-name" "$CLIENT_NAME")
  [ -n "$TEST_EMAIL" ] && SETUP_ARGS+=("--test-email" "$TEST_EMAIL")
  [ -n "$TEST_PASSWORD" ] && SETUP_ARGS+=("--test-password" "$TEST_PASSWORD")
  [ -n "$CSV_PATH" ] && SETUP_ARGS+=("--csv-path" "$CSV_PATH")
  [ "$SKIP_TEST_DATA" = "true" ] && SETUP_ARGS+=("--skip-test-data")
  [ "$SKIP_CSV_IMPORT" = "true" ] && SETUP_ARGS+=("--skip-csv-import")
  
  # Run setup script (migrations already done, but alembic is idempotent)
  bash /app/setup.sh "${SETUP_ARGS[@]}" || echo "Setup completed with warnings"
else
  echo "Existing database detected, skipping first-time setup"
fi

# Start the application
echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
