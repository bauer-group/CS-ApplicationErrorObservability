# Bugsink Configuration Guide

This document provides a comprehensive reference for all configuration options available in this Bugsink deployment.

## Table of Contents

- [Common Settings](#common-settings)
- [Site Configuration](#site-configuration)
- [Database Settings](#database-settings)
- [Network Settings](#network-settings)
- [Traefik Proxy Settings](#traefik-proxy-settings)
- [Application Secrets](#application-secrets)
- [Initial Admin User](#initial-admin-user)
- [User Registration & Permissions](#user-registration--permissions)
- [Email Configuration (SMTP)](#email-configuration-smtp)
- [Rate Limits & Maximums](#rate-limits--maximums)
- [Background Worker](#background-worker)
- [Privacy & Debugging](#privacy--debugging)

---

## Common Settings

### `STACK_NAME`

**Default:** `bugsink_app_example_com`

A unique identifier for this Docker Compose stack. This name is used for:

- Container naming (`${STACK_NAME}_SERVER`, `${STACK_NAME}_DATABASE`)
- Volume naming (`${STACK_NAME}-postgres`)
- Network naming
- Traefik router/middleware naming

Use underscores instead of dots or hyphens for best compatibility. Example: `bugsink_prod_company_com`

### `BUGSINK_VERSION`

**Default:** `2`

The Bugsink Docker image version to use. Check [Docker Hub](https://hub.docker.com/r/bugsink/bugsink/tags) for available versions.

### `TIME_ZONE`

**Default:** `UTC`

The default time zone for displaying dates and times throughout the application. Uses IANA time zone names.

**Examples:**
- `UTC`
- `Europe/Berlin`
- `America/New_York`
- `Asia/Tokyo`

This setting affects both the application and the PostgreSQL database (`TZ` and `PG_TZ`).

---

## Site Configuration

### `SITE_TITLE`

**Default:** `Bugsink`

A customizable title for your Bugsink instance. This is particularly useful when running multiple Bugsink instances (e.g., staging vs. production).

**Examples:**
- `Bugsink [COMPANY NAME]`
- `Bugsink (Staging)`
- `Bugsink (Production)`
- `ACME Corp Error Tracking`

---

## Database Settings

This deployment uses PostgreSQL 18 with performance optimizations for SSD/NVMe storage.

### `POSTGRES_VERSION`

**Default:** `18`

The PostgreSQL major version to use. This deployment includes extensive tuning parameters optimized for modern hardware.

### `DATABASE_POOLMAXSIZE`

**Default:** `100`

Maximum number of database connections allowed. This maps to PostgreSQL's `max_connections` parameter. Increase this value if you experience connection pool exhaustion under heavy load.

### `DATABASE_PASSWORD`

**Required** - No default

The password for the PostgreSQL `bugsink` user. Generate a secure password:

```bash
openssl rand -base64 32
```

### PostgreSQL Tuning Parameters

The following parameters are pre-configured in `docker-compose.yml` for optimal performance on systems with 4-8 GB RAM and SSD/NVMe storage:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `shared_buffers` | 512MB | Memory for caching data |
| `work_mem` | 4MB | Memory per operation (sorts, joins) |
| `effective_cache_size` | 1536MB | Planner's assumption of available cache |
| `maintenance_work_mem` | 128MB | Memory for maintenance operations |
| `max_wal_size` | 1GB | Maximum WAL size before checkpoint |
| `min_wal_size` | 256MB | Minimum WAL size to retain |
| `random_page_cost` | 1.1 | Cost estimate for random disk access (SSD optimized) |
| `effective_io_concurrency` | 200 | Concurrent I/O operations (SSD optimized) |
| `max_parallel_workers` | 4 | Total parallel worker processes |
| `checkpoint_completion_target` | 0.9 | Spread checkpoint I/O over time |
| `wal_buffers` | 16MB | Memory for WAL data |

---

## Network Settings

### `PRIVATESUBNET`

**Default:** `254`

A unique subnet identifier (1-254) used to create isolated Docker networks for this stack. This prevents IP conflicts when running multiple Docker Compose stacks.

The subnet configuration creates:
- **IPv4:** `10.99.${PRIVATESUBNET}.0/24`
- **IPv6:** `fdfd:10:99:${PRIVATESUBNET}::/64`

**Important:** Choose a unique value for each stack to avoid network conflicts.

---

## Traefik Proxy Settings

This deployment is designed to run behind a Traefik reverse proxy with automatic HTTPS via Let's Encrypt.

### `SERVICE_HOSTNAME`

**Required** - No default

The fully qualified domain name where Bugsink will be accessible. DNS must resolve to your Traefik proxy server.

**Example:** `bugsink.app.example.com`

This value is used for:
- Traefik routing rules
- Bugsink's `BASE_URL` configuration
- Django's `ALLOWED_HOSTS` setting
- DSN generation for Sentry SDKs

### `PROXY_NETWORK`

**Default:** `traefik`

The name of the external Docker network where Traefik is running. The Bugsink container joins this network to receive proxied traffic.

**Common values:**
- `traefik`
- `EDGEPROXY`
- `proxy`

### Traefik Labels

The deployment automatically configures:

- HTTP to HTTPS redirect (301 permanent)
- TLS termination with Let's Encrypt (`certresolver=letsencrypt`)
- Proper service routing on port 8000

---

## Application Secrets

### `SECRET_KEY`

**Required** - No default

Django's secret key used for cryptographic signing (sessions, CSRF tokens, etc.). Must be at least 50 characters of random data.

**Generate with:**
```bash
openssl rand -base64 50
```

**Security Warning:** Never commit this value to version control. Never reuse keys across environments.

---

## Initial Admin User

### `CREATE_SUPERUSER`

**Default:** Empty (disabled)

**Format:** `email:password`

Creates an initial superuser account on first container start. The user is only created if no users exist in the database.

**Example:** `admin@example.com:MySecurePassword123!`

**Security Best Practice:**
1. Set this value for initial deployment
2. Start the container and log in
3. Remove this variable from `.env`
4. Restart the container

This prevents the credentials from being stored in configuration files long-term.

---

## User Registration & Permissions

### `SINGLE_USER`

**Default:** `false`

When set to `true`, disables all multi-user functionality:
- User registration
- Teams
- Project membership

Use this for personal/single-developer instances.

### `SINGLE_TEAM`

**Default:** `false`

When set to `true`, all users belong to a single shared team. This simplifies permission management for small teams where everyone should have access to all projects.

### `USER_REGISTRATION`

**Default:** `CB_ADMINS`

Controls who can register new user accounts:

| Value | Description |
|-------|-------------|
| `CB_ANYBODY` | Anyone can sign up without approval. **Warning:** Only use behind firewall/VPN! |
| `CB_MEMBERS` | Any existing user can invite new users via email |
| `CB_ADMINS` | Only admin users can invite new users |
| `CB_NOBODY` | User registration completely disabled |

**Security Recommendation:** Use `CB_ADMINS` or `CB_MEMBERS` for internet-facing instances.

### `USER_REGISTRATION_VERIFY_EMAIL`

**Default:** `true`

When enabled, new users must verify their email address before they can log in. This prevents:
- Typos in email addresses
- Spam/fake accounts
- Unauthorized access via guessed emails

### `TEAM_CREATION`

**Default:** `CB_ADMINS`

Controls who can create new teams:

| Value | Description |
|-------|-------------|
| `CB_MEMBERS` | Any user can create teams |
| `CB_ADMINS` | Only admin users can create teams |
| `CB_NOBODY` | Team creation disabled |

---

## Email Configuration (SMTP)

Email is required for:
- Password reset functionality
- User invitations
- Issue notifications
- Alert emails

### `EMAIL_HOST`

**Required for email** - No default

The SMTP server hostname.

**Examples:**
- `smtp.gmail.com`
- `smtp.office365.com`
- `email-smtp.eu-west-1.amazonaws.com` (AWS SES)
- `smtp.sendgrid.net`

### `EMAIL_PORT`

**Default:** `587`

The SMTP server port. Common values:
- `587` - STARTTLS (recommended)
- `465` - Implicit SSL/TLS
- `25` - Unencrypted (not recommended)

### `EMAIL_HOST_USER`

**Required for email** - No default

The username for SMTP authentication. Often the full email address.

### `EMAIL_HOST_PASSWORD`

**Required for email** - No default

The password or API key for SMTP authentication.

**For services like Gmail:** Use an App Password, not your regular password.

### `EMAIL_USE_TLS`

**Default:** `true`

Enable STARTTLS encryption. Used with port 587. Mutually exclusive with `EMAIL_USE_SSL`.

### `EMAIL_USE_SSL`

**Default:** `false`

Enable implicit SSL/TLS encryption. Used with port 465. Mutually exclusive with `EMAIL_USE_TLS`.

### `EMAIL_TIMEOUT`

**Default:** `5`

Connection timeout in seconds for SMTP operations.

### `DEFAULT_FROM_EMAIL`

**Required for email** - No default

The "From" address for all outgoing emails.

**Format:** `Display Name <email@example.com>`

**Example:** `Bugsink <noreply@example.com>`

**Important:** Use an address that matches your domain's SPF/DKIM records to avoid spam filtering.

### `EMAIL_LOGGING`

**Default:** `false`

When enabled, logs the subject and recipients of each sent email to the container logs. Useful for debugging email delivery issues.

---

## Rate Limits & Maximums

These settings protect against accidental abuse and resource exhaustion.

### `MAX_EVENT_SIZE`

**Default:** `1048576` (1 MB)

Maximum size of a single event that Bugsink will process. Events larger than this are rejected.

### `MAX_ENVELOPE_SIZE`

**Default:** `104857600` (100 MB)

Maximum size of an envelope (which may contain multiple events) that Bugsink will process.

### `MAX_ENVELOPE_COMPRESSED_SIZE`

**Default:** `20971520` (20 MB)

Maximum size of a compressed envelope before decompression.

### `MAX_EVENTS_PER_PROJECT_PER_5_MINUTES`

**Default:** `1000`

Rate limit: Maximum events a single project can submit in 5 minutes. Exceeding this triggers rate limiting responses to the SDK.

### `MAX_EVENTS_PER_PROJECT_PER_HOUR`

**Default:** `5000`

Rate limit: Maximum events a single project can submit per hour.

### `MAX_EMAILS_PER_MONTH`

**Default:** Empty (unlimited)

Optional quota for total emails sent by the Bugsink instance per month. Useful for controlling costs with transactional email services.

**Example:** `10000`

---

## Background Worker

Bugsink uses a background worker (snappea) for processing events and sending emails asynchronously.

### `TASK_ALWAYS_EAGER`

**Default:** `false`

| Value | Behavior |
|-------|----------|
| `false` | Tasks run in background worker (production) |
| `true` | Tasks run inline in request/response (development only) |

**Warning:** Setting to `true` in production will cause slow responses and potential timeouts.

### `SNAPPEA_NUM_WORKERS`

**Default:** `2`

Number of worker threads in the background worker process. Event processing is serial, so values of 2-4 are typically optimal.

---

## Privacy & Debugging

### `PHONEHOME`

**Default:** `false`

Controls telemetry to bugsink.com. When enabled, sends basic installation statistics (version, event counts) to help the Bugsink developers understand usage patterns.

Set to `false` for complete privacy.

### `DEBUG`

**Default:** `false`

Enables Django debug mode. **Never enable in production** as it exposes sensitive information in error pages.

---

## Quick Reference: Byte Values

| Human Readable | Bytes |
|----------------|-------|
| 1 MB | `1048576` |
| 10 MB | `10485760` |
| 20 MB | `20971520` |
| 50 MB | `52428800` |
| 100 MB | `104857600` |

---

## Environment File Security

The `.env` file contains sensitive credentials. Ensure proper security:

```bash
# Set restrictive permissions
chmod 600 .env

# Never commit to version control
echo ".env" >> .gitignore
```

---

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Sentry SDK Integration](sentry-sdk-integration.md)
