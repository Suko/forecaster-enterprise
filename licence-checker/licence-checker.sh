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
else
    # Treat initial failure as the first fail count
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initial check failed - fail $FAIL_COUNT/$MAX_FAILS"
fi

while true; do
    sleep "$CHECK_INTERVAL"

    if check_license; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] License valid ✓"
        FAIL_COUNT=0
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] License invalid or unreachable – fail $FAIL_COUNT/$MAX_FAILS"

        if [ "$FAIL_COUNT" -ge "$MAX_FAILS" ]; then
            echo "GRACE PERIOD EXPIRED – shutting down containers..."
            
            # Use docker ps -f instead of --filter for explicit filtering syntax
            # -q: only show IDs
            # -a: include stopped containers (in case something stopped between checks)
            CONTAINER_IDS=$(docker ps -qa -f "label=com.forecasting.license=true")
            
            if [ -n "$CONTAINER_IDS" ]; then
                # Use plain docker stop with IDs instead of xargs for clarity
                echo "$CONTAINER_IDS" | xargs docker stop -t 20 
            else
                echo "No labeled containers found to stop."
            fi

            echo "Containers stopped. License watcher exiting."
            exit 0
        fi
    fi
done