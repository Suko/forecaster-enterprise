# License Checker System

A secure, lightweight, and production-grade license validation system for Docker-based applications. When the license is invalid, revoked, expired, or unreachable for too long, the licensed containers (backend + database) are automatically stopped while the frontend remains running to display a license error page.

## Architecture

```
Customer Environment
├── docker-compose.yml
├── frontend (keeps running to show error page)
│   └─→ reads /license-data/license-status.json
├── backend  (stopped on license failure)
├── db       (stopped on license failure)
└── licence-watcher (this container)
    ├─→ writes /license-data/license-status.json (shared volume)
    └─→ POST → https://<your-project>.supabase.co/functions/v1/check-license
        └─→ On prolonged failure → stops containers with label: forecast.license.stop=true
        └─→ On license renewal  → auto-restarts containers (waits for healthy)

Your Infrastructure (Supabase)
├── Edge Function: check-license
├── Tables: licenses, activations
└── RPCs: check_rate_limit, activate_device_transactional
```

## Features

- **Persistent machine ID** - Stored in Docker volume
- **Configurable check interval** - Default: 1 hour
- **Configurable grace period** - Default: 48 hours
- **License status file** - Shared with frontend via Docker volume
- **Graceful degradation** - Frontend shows license error page while backend is stopped
- **Automatic container shutdown** - Only labeled containers after grace period expires
- **Auto-restart on renewal** - Services resume when license becomes valid again
- **Health-aware restart** - Waits for db and backend to be healthy before notifying frontend
- **Stale file detection** - Frontend treats old status files as invalid (prevents bypass)
- **Device-limit enforcement** - `max_machines` per license
- **Rate limiting** - 5 requests/min per IP
- **Transactional activation** - No race conditions
- **Tiny image** - < 15 MB
- **Zero runtime dependencies** - Self-contained

## Environment Variables

Create a `.env` file with the following variables:

```env
# Required
LICENSE_URL=https://your-project.supabase.co/functions/v1/check-license
LICENSE_KEY=xyz

# Optional (defaults shown)
CHECK_INTERVAL=3600     # Seconds between checks
GRACE_PERIOD=172800     # Seconds of allowed failures (48 hours)
```

## Docker Labels

To enable license enforcement, add the following label to containers that should be stopped when the license expires. Containers without this label (e.g., frontend) will keep running.

```yaml
services:
  db:
    image: postgres:16-alpine
    labels:
      - "forecast.license.stop=true"
    # ...

  backend:
    build: ./backend
    labels:
      - "forecast.license.stop=true"
    # ...

  frontend:
    build: ./frontend
    volumes:
      - license_data:/license-data:ro # Read license status file
    # No license label - keeps running to show error page
    # ...

  license-watcher:
    build: ./licence-checker
    volumes:
      - license_data:/license-data # Write license status file
      - /var/run/docker.sock:/var/run/docker.sock:ro
    # ...

volumes:
  license_data:
```

## License Status File

The license-watcher writes a JSON status file to a shared Docker volume. The frontend reads this file to determine whether to show the license error page.

**File path:** `/license-data/license-status.json`

**Valid license:**

```json
{ "valid": true, "checkedAt": "2025-12-11T10:30:00Z" }
```

**Expired license:**

```json
{ "valid": false, "reason": "expired", "checkedAt": "2025-12-11T10:30:00Z" }
```

The frontend considers the status invalid if:

- File doesn't exist (license-watcher not running)
- File is older than `GRACE_PERIOD` (license-watcher stopped)
- `valid` is `false`

## Supabase Edge Function

The Edge Function expects and returns the following JSON payloads:

### Request

```json
{
  "machine_id": "a1b2c3d4-e5f6-...",
  "license_key": "lk-..."
}
```

### Success Response

```json
{
  "valid": true,
  "expires": "2026-12-31T00:00:00Z"
}
```

### Error Response

```json
{
  "valid": false,
  "error": "License Expired"
}
```

## Supabase Database Schema

### Tables

```sql
-- Licenses
CREATE TABLE licenses (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  activation_key text UNIQUE NOT NULL,
  max_machines int NOT NULL DEFAULT 1,
  expires_at timestamptz,
  is_active boolean DEFAULT true
);

-- Activations
CREATE TABLE activations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  license_id uuid REFERENCES licenses(id) ON DELETE CASCADE,
  machine_id text NOT NULL,
  last_check_in timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  UNIQUE(license_id, machine_id)
);
```

### Required RPC Functions

You need to create two PostgreSQL functions:

1. `check_rate_limit(user_ip text, limit_count int, window_seconds int)`
2. `activate_device_safe(p_license_id uuid, p_machine_id text, p_max_machines int)`

## Deployment

### Customer Deployment

Send your customer:

- Docker image
- Their unique `LICENSE_KEY`
- The correct `LICENSE_URL`

Customer runs:

```bash
docker compose up -d
```

## Troubleshooting

| Issue                     | Watcher Log Message                                                         | Solution                                                                                                           |
| ------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Dependency Fail**       | `ERROR: Required commands (curl, jq...) are not found.`                     | Ensure the base Docker image for the watcher includes these packages (`apk add curl jq`).                          |
| **API Error**             | `HTTP Error: 400` or `License Check Failed (Status 400)...`                 | Check Supabase logs. The error is an invalid key, expired license, rate limit, or device limit reached.            |
| **Shutdown Triggered**    | `GRACE PERIOD EXPIRED – stopping licensed services...`                      | The license is confirmed invalid/expired, and the grace period has run out. Re-enable or renew the license key.    |
| **Auto-Restart**          | `License renewed! Restarting services...`                                   | License became valid again - services auto-restart.                                                                |
| **Cannot Control Docker** | `Got permission denied while trying to connect to the Docker daemon socket` | Check host permissions for `/var/run/docker.sock` or ensure the file is mounted correctly and the user has access. |

## License Expiration Flow

1. License check fails → grace period countdown starts
2. Subsequent checks continue to fail → fail count increases
3. Grace period expires → containers with `forecast.license.stop=true` label are stopped
4. Status file updated to `{"valid": false, "reason": "expired"}`
5. Frontend reads status file → redirects users to `/license-error` page
6. License watcher continues running → monitors for license renewal
7. License becomes valid → db container started, wait for healthy
8. Backend container started → wait for healthy
9. Status file updated to `{"valid": true}` only after services are healthy
10. Frontend reads status file → redirects users to home page

## Security

- ✅ `SUPABASE_SERVICE_ROLE_KEY` remains secret (only in Edge Function)
- ✅ Docker socket is mounted read-only with minimal permissions
- ✅ All communication over HTTPS
- ✅ Machine ID persists across container restarts (stored in volume)
- ✅ Rate limiting prevents brute-force attacks
- ✅ Transactional device activation prevents race conditions
- ✅ Stale status file detection prevents license-watcher bypass
- ✅ Frontend assumes invalid if status file missing or stale
