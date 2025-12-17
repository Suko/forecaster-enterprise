#!/bin/sh
set -euo pipefail

# === Temporary File Management ===
# Create a secure temporary file to store the API response.
LICENSE_RESPONSE_FILE=$(mktemp) || { echo "ERROR: Failed to create temporary file." >&2; exit 1; }

# TRAP: Ensure the temporary file is deleted upon exit, crash, or interrupt.
# EXIT: on normal exit (0) or error exit (1)
# INT: on Ctrl+C interrupt
# TERM: on SIGTERM (standard Docker stop signal)
trap "rm -f $LICENSE_RESPONSE_FILE" EXIT INT TERM

# === Config – all overridable via environment ===
LICENSE_URL="${LICENSE_URL:-}"
CHECK_INTERVAL="${CHECK_INTERVAL:-3600}" # seconds
GRACE_PERIOD="${GRACE_PERIOD:-172800}" # seconds (default 48h)
LICENSE_KEY="${LICENSE_KEY:-}"

# === Dependencies Check ===
if ! command -v curl >/dev/null || ! command -v jq >/dev/null || ! command -v uuidgen >/dev/null || ! command -v docker >/dev/null; then
    echo "ERROR: Required commands (curl, jq, uuidgen, docker) are not found."
    exit 1
fi

if [ -z "$LICENSE_URL" ]; then
    echo "ERROR: LICENSE_URL is not set!"
    exit 1
fi

if [ -z "$LICENSE_KEY" ]; then
    echo "ERROR: LICENSE_KEY is not set!"
    exit 1
fi

# === Persistent machine ID ===
mkdir -p /data
if [ ! -f /data/machine_id ]; then
    # Generate UUID and store it, ensuring it's lower-case
    uuidgen | tr '[:upper:]' '[:lower:]' > /data/machine_id
fi
MACHINE_ID=$(cat /data/machine_id)

echo "========================================"
echo "License Watcher Started"
echo "Machine ID   : $MACHINE_ID"
echo "Endpoint     : $LICENSE_URL"
echo "Check every  : ${CHECK_INTERVAL}s"
echo "Grace period : ${GRACE_PERIOD}s (~$((GRACE_PERIOD/86400)) days)"
echo "========================================"

# Calculate fail limits
FAIL_COUNT=0
MAX_FAILS=$((GRACE_PERIOD / CHECK_INTERVAL))

# Ensure max fails is at least 1
if [ "$MAX_FAILS" -lt 1 ]; then
    MAX_FAILS=1
fi

# === License Status File ===
# This file is read by the frontend to show license status to users
mkdir -p /license-data
LICENSE_STATUS_FILE="/license-data/license-status.json"

# Write license status to shared file (read by frontend)
write_status() {
    local valid="$1"
    local reason="${2:-}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    if [ "$valid" = "true" ]; then
        cat > "$LICENSE_STATUS_FILE" <<EOF
{"valid":true,"checkedAt":"$timestamp","machineId":"$MACHINE_ID"}
EOF
    else
        cat > "$LICENSE_STATUS_FILE" <<EOF
{"valid":false,"reason":"$reason","checkedAt":"$timestamp","machineId":"$MACHINE_ID"}
EOF
    fi
}

# Initialize status file as valid (optimistic start)
write_status "true"

# --- License Check Function ---
check_license() {
    # Perform CURL request, capture response code, and save body to temp file.
    # -w "%{http_code}" prints the code to stdout; -o redirects the body to the file.
    RESPONSE_CODE=$(
        curl -sSfL -m 20 -w "%{http_code}" "$LICENSE_URL" \
            -H "Content-Type: application/json" \
            --data "{\"machine_id\":\"$MACHINE_ID\", \"license_key\":\"$LICENSE_KEY\"}" \
            -o "$LICENSE_RESPONSE_FILE"
    )
    
    # Check 1: Did the HTTP request succeed (2xx)?
    if [ "$RESPONSE_CODE" -lt 200 ] || [ "$RESPONSE_CODE" -ge 300 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] HTTP Error: $RESPONSE_CODE" >&2
		# Log response body for debugging 4xx/5xx errors
        cat "$LICENSE_RESPONSE_FILE" >&2 || true
        return 1
    fi

    # Check 2: Was the response valid JSON containing "valid: true"?
    if jq -e '.valid == true' "$LICENSE_RESPONSE_FILE" >/dev/null 2>&1; then
        return 0 # Success: valid is true
    else
        # If jq fails, it means 'valid' is false, or the JSON format is bad.
        ERROR_MSG=$(jq -r '.error // "API response does not contain valid=true or has bad JSON structure."' "$LICENSE_RESPONSE_FILE")
        echo "License Check Failed (Status $RESPONSE_CODE): $ERROR_MSG"
        return 1
    fi
}

# --- Main Loop ---

# Perform an immediate check before the first sleep
check_license
CHECK_STATUS=$?

if [ "$CHECK_STATUS" -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initial license check success ✓"
    write_status "true"
else
    # Treat initial failure as the first fail count
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initial check failed - fail $FAIL_COUNT/$MAX_FAILS"
fi

# Track if services were stopped due to license
SERVICES_STOPPED=false
LICENSE_LABEL="forecast.license.stop=true"

while true; do
    sleep "$CHECK_INTERVAL"

    if check_license; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] License valid ✓"
        FAIL_COUNT=0
        
        # Auto-restart services if they were stopped due to license and license is now valid
        if [ "$SERVICES_STOPPED" = true ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] License renewed! Restarting services..."
            STOPPED_CONTAINERS=$(docker ps -qa -f "label=$LICENSE_LABEL")
            if [ -n "$STOPPED_CONTAINERS" ]; then
                # Start db first, then backend (respects dependency order)
                # Get container names to start in correct order
                DB_CONTAINER=$(docker ps -qa -f "label=$LICENSE_LABEL" -f "name=db")
                BACKEND_CONTAINER=$(docker ps -qa -f "label=$LICENSE_LABEL" -f "name=backend")
                
                # Start db first
                if [ -n "$DB_CONTAINER" ]; then
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting database..."
                    docker start "$DB_CONTAINER"
                    
                    # Wait for db to be healthy (max 60s)
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for database to be healthy..."
                    for i in $(seq 1 30); do
                        if docker inspect --format='{{.State.Health.Status}}' "$DB_CONTAINER" 2>/dev/null | grep -q "healthy"; then
                            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Database healthy ✓"
                            break
                        fi
                        sleep 2
                    done
                fi
                
                # Then start backend
                if [ -n "$BACKEND_CONTAINER" ]; then
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backend..."
                    docker start "$BACKEND_CONTAINER"
                    
                    # Wait for backend to be healthy (max 90s - it has start_period: 60s)
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for backend to be healthy..."
                    for i in $(seq 1 45); do
                        if docker inspect --format='{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null | grep -q "healthy"; then
                            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backend healthy ✓"
                            break
                        fi
                        sleep 2
                    done
                fi
                
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Services restarted ✓"
                SERVICES_STOPPED=false
                # Only write valid status after services are healthy
                write_status "true"
            fi
        else
            # Services already running, just update status
            write_status "true"
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] License invalid or unreachable – fail $FAIL_COUNT/$MAX_FAILS"

        if [ "$FAIL_COUNT" -ge "$MAX_FAILS" ] && [ "$SERVICES_STOPPED" = false ]; then
            echo "GRACE PERIOD EXPIRED – stopping licensed services..."
            
            # Stop all containers with the license label (backend + db)
            # Frontend stays running to show license error page
            CONTAINERS_TO_STOP=$(docker ps -q -f "label=$LICENSE_LABEL")
            
            if [ -n "$CONTAINERS_TO_STOP" ]; then
                for CONTAINER in $CONTAINERS_TO_STOP; do
                    CONTAINER_NAME=$(docker inspect --format '{{.Name}}' "$CONTAINER" | sed 's/^\///')
                    echo "Stopping container: $CONTAINER_NAME ($CONTAINER)"
                    docker stop -t 10 "$CONTAINER"
                done
                echo "Licensed services stopped. Frontend will display license error."
                SERVICES_STOPPED=true
                write_status "false" "expired"
            else
                echo "No containers with label $LICENSE_LABEL found."
            fi

            # Keep license-watcher running to allow recovery if license is renewed
            echo "License watcher will continue checking for license renewal..."
            echo "Services will auto-restart when license becomes valid again."
        fi
    fi
done