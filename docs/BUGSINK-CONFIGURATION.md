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

Controls who can register new user accounts. This is one of the most important security settings.

| Value | Description | Use Case |
|-------|-------------|----------|
| `CB_ANYBODY` | Anyone can sign up without approval | **Dangerous!** Only for internal networks behind firewall/VPN |
| `CB_MEMBERS` | Any existing user can invite new users | Self-service teams, moderate control |
| `CB_ADMINS` | Only admin users can invite new users | Corporate environments, strict control |
| `CB_NOBODY` | User registration completely disabled | Locked-down instances, no new users |

#### Detailed Explanation

**`CB_ANYBODY` - Open Registration**
```
Login Page → "Sign Up" link visible → Anyone can create account
```
- New users see a "Sign up" link on the login page
- They can create an account with just an email and password
- No approval or invitation required
- **Security Risk:** If exposed to the internet, anyone can create accounts
- **Safe Use:** Behind VPN, firewall, or IP whitelist

**`CB_MEMBERS` - Member Invitations**
```
Existing User → Invite to Team/Project → Enter email → New user receives invite
```
- No public "Sign up" link on login page
- Any existing user can invite new users
- Invitation happens when adding members to a team or project
- If the email isn't registered, an invitation is sent
- Good for growing teams where trust is distributed

**`CB_ADMINS` - Admin-Only Invitations**
```
Admin User → Invite to Team/Project → Enter email → New user receives invite
```
- No public "Sign up" link on login page
- Only users with "Admin" role can invite new users
- Regular users can only add existing users to teams/projects
- Best for corporate environments with controlled access
- **Recommended for most production deployments**

**`CB_NOBODY` - No Registration**
```
No new users can be created (except via CREATE_SUPERUSER or CLI)
```
- No public "Sign up" link
- No invitation capability for anyone
- Existing users remain active
- New users can only be created via:
  - `CREATE_SUPERUSER` environment variable
  - Django management command (`createsuperuser`)
- Use for fully locked-down instances

#### Decision Matrix

| Scenario | Recommended Setting |
|----------|---------------------|
| Personal instance | `SINGLE_USER=true` |
| Small trusted team | `CB_MEMBERS` |
| Corporate/Enterprise | `CB_ADMINS` |
| Public internet, no VPN | `CB_ADMINS` or `CB_NOBODY` |
| Behind VPN/Firewall | `CB_ANYBODY` is acceptable |
| Compliance requirements | `CB_ADMINS` with `USER_REGISTRATION_VERIFY_EMAIL=true` |

### `USER_REGISTRATION_VERIFY_EMAIL`

**Default:** `true`

When enabled, new users must verify their email address before they can log in.

**How it works:**
1. User receives invitation or signs up
2. Verification email is sent with a unique link
3. User clicks link to verify email
4. Only then can user set password and log in

**Benefits:**
- Confirms email address is valid and accessible
- Prevents typos in email addresses
- Blocks spam/fake account creation
- Required for password reset to work

**When to disable:**
- Internal networks where email isn't configured
- Development/testing environments
- When using SSO/OIDC (users already verified)

### `USER_REGISTRATION_VERIFY_EMAIL_EXPIRY`

**Default:** `86400` (24 hours)

Time in seconds that the email verification link remains valid.

| Duration | Seconds |
|----------|---------|
| 1 hour | `3600` |
| 12 hours | `43200` |
| 24 hours | `86400` |
| 48 hours | `172800` |
| 7 days | `604800` |

If a user doesn't verify within this time, they must request a new invitation.

### `TEAM_CREATION`

**Default:** `CB_ADMINS`

Controls who can create new teams. Teams are organizational units that group projects and users.

| Value | Description | Use Case |
|-------|-------------|----------|
| `CB_MEMBERS` | Any user can create teams | Self-organizing teams, startups |
| `CB_ADMINS` | Only admin users can create teams | Controlled structure |
| `CB_NOBODY` | Team creation disabled | Single-team mode, use with `SINGLE_TEAM=true` |

**Note:** If `SINGLE_TEAM=true`, this setting is ignored since there's only one team.

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

**Important:** Rate limits are applied **per project**, not globally.

### Understanding Rate Limits for Multi-Project Instances

When planning capacity, consider that limits apply per project:

| Projects | Events/5min | Theoretical Max/5min | Events/hour | Theoretical Max/hour |
|----------|-------------|----------------------|-------------|----------------------|
| 10       | 2,500       | 25,000               | 15,000      | 150,000              |
| 50       | 2,500       | 125,000              | 15,000      | 750,000              |
| 100      | 2,500       | 250,000              | 15,000      | 1,500,000            |
| 200      | 2,500       | 500,000              | 15,000      | 3,000,000            |

**In practice:** Not all projects will hit limits simultaneously. Typical usage is 5-10% of theoretical maximum.

### Sizing Guide

| Instance Size | Projects | Events/5min | Events/hour | Workers |
|---------------|----------|-------------|-------------|---------|
| Small         | 1-10     | 1,000       | 5,000       | 2       |
| Medium        | 10-50    | 2,500       | 15,000      | 4       |
| Large         | 50-200   | 2,500       | 15,000      | 4-6     |
| XLarge        | 200+     | 1,500       | 10,000      | 6-8     |

**Note:** For very large instances (200+ projects), consider **reducing** per-project limits to protect overall system stability. A runaway error loop in one project shouldn't impact others.

### `MAX_EVENT_SIZE`

**Default:** `2097152` (2 MB)

Maximum size of a single event that Bugsink will process. Events larger than this are rejected.

**Considerations:**

- 1 MB is sufficient for most errors
- 2 MB allows for larger stack traces and local variables
- Increase to 5-10 MB only if you use Python's extended local variable capture

**Byte values:**

| Size  | Bytes      |
|-------|------------|
| 1 MB  | `1048576`  |
| 2 MB  | `2097152`  |
| 5 MB  | `5242880`  |
| 10 MB | `10485760` |

### `MAX_ENVELOPE_SIZE`

**Default:** `104857600` (100 MB)

Maximum size of an envelope (which may contain multiple events) that Bugsink will process. An envelope is a batch of events sent together by the SDK.

### `MAX_ENVELOPE_COMPRESSED_SIZE`

**Default:** `20971520` (20 MB)

Maximum size of a compressed envelope before decompression. SDKs typically compress envelopes before sending.

### `MAX_EVENTS_PER_PROJECT_PER_5_MINUTES`

**Default:** `2500`

Rate limit: Maximum events a single project can submit in 5 minutes. Exceeding this triggers rate limiting responses (HTTP 429) to the SDK.

**Why this matters:**

- Protects against "error storms" (e.g., a bug in a loop generating millions of identical errors)
- Prevents one misbehaving project from consuming all resources
- SDKs handle 429 responses gracefully by backing off

**Tuning:**

```text
Events/minute = MAX_EVENTS_PER_PROJECT_PER_5_MINUTES / 5
```

- Default 2,500 = 500 events/minute per project
- Sufficient for most production workloads
- Reduce for very large instances (200+ projects)

### `MAX_EVENTS_PER_PROJECT_PER_HOUR`

**Default:** `15000`

Rate limit: Maximum events a single project can submit per hour. This is a secondary limit that catches sustained high volume.

**Tuning:**

```text
Events/minute = MAX_EVENTS_PER_PROJECT_PER_HOUR / 60
```

- Default 15,000 = 250 events/minute sustained per project
- Lower than the 5-minute burst rate to prevent sustained abuse
- Increase if legitimate high-volume projects need more headroom

### `MAX_EMAILS_PER_MONTH`

**Default:** Empty (unlimited)

Optional quota for total emails sent by the Bugsink instance per month. This is a **global** limit, not per project.

**Use cases:**

- Control costs with transactional email services (SendGrid, Mailgun, etc.)
- Prevent email spam if a project generates excessive alerts

**Example values:**

- Small instance: `10000`
- Medium instance: `50000`
- Large instance: `100000` or unlimited

### Rate Limit Best Practices

1. **Start with defaults** - They work well for most installations
2. **Monitor before adjusting** - Watch for 429 responses in logs
3. **Increase gradually** - Double limits if hitting them legitimately
4. **Consider per-project variation** - Some projects may need higher limits
5. **Plan for incidents** - A production incident can spike errors 100x

### What Happens When Limits Are Hit

1. SDK receives HTTP 429 (Too Many Requests)
2. SDK backs off and retries with exponential delay
3. Some events may be dropped if backpressure continues
4. Bugsink logs rate limit events for monitoring

**Monitoring rate limits:**

```bash
docker compose logs bugsink-server | grep -i "rate limit"
```

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
