# License Checker System

A secure, lightweight, and production-grade license validation system for Docker-based applications. When the license is invalid, revoked, expired, or unreachable for too long, the protected containers are automatically stopped.

## Architecture

```
Customer Environment
├── docker-compose.yml
└── licence-watcher (this container)
    └─→ POST → https://<your-project>.supabase.co/functions/v1/check-license
        └─→ On prolonged failure → stops containers with label: com.myapp.license=true

Your Infrastructure (Supabase)
├── Edge Function: check-license
├── Tables: licenses, activations
└── RPCs: check_rate_limit, activate_device_transactional
```

## Features

- **Persistent machine ID** - Stored in Docker volume
- **Configurable check interval** - Default: 1 hour
- **Configurable grace period** - Default: 48 hours
- **Automatic container shutdown** - After grace period expires
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

## Docker

To enable enforcement, every protected application container must be launched with the following Docker label. This label is the filter used by the watcher to stop your application containers.

```YAML
labels:
  com.forecasting.license: "true"
```

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
| **Shutdown Triggered**    | `GRACE PERIOD EXPIRED – shutting down containers...`                        | The license is confirmed invalid/expired, and the grace period has run out. Re-enable or renew the license key.    |
| **Cannot Control Docker** | `Got permission denied while trying to connect to the Docker daemon socket` | Check host permissions for `/var/run/docker.sock` or ensure the file is mounted correctly and the user has access. |

## Security

- ✅ `SUPABASE_SERVICE_ROLE_KEY` remains secret (only in Edge Function)
- ✅ Docker socket is mounted read-only with minimal permissions
- ✅ All communication over HTTPS
- ✅ Machine ID persists across container restarts (stored in volume)
- ✅ Rate limiting prevents brute-force attacks
- ✅ Transactional device activation prevents race conditions
