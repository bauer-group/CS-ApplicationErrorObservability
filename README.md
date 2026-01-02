# Error Observability

Self-hosted error tracking solution based on [Bugsink](https://bugsink.com/) - a lightweight, Sentry-compatible error monitoring platform.

## Features

- **Sentry SDK Compatible** - Works with all official Sentry SDKs (Python, JavaScript, PHP, Go, Ruby, Java, .NET, Rust, etc.)
- **Self-Hosted** - Your data stays on your infrastructure
- **PostgreSQL 18** - Performance-tuned database with SSD/NVMe optimizations
- **Multi-Project Support** - Optimized for ~100 projects per instance
- **Traefik Integration** - Automatic HTTPS with Let's Encrypt
- **Dual-Stack Networking** - IPv4 + IPv6 support

## Quick Start

### 1. Generate Configuration

```bash
# Windows
tools\run.cmd
./scripts/generate-secrets.sh

# Linux/macOS
./tools/run.sh
./scripts/generate-secrets.sh
```

This creates `.env` from `.env.example` with secure random values for:
- `SECRET_KEY` - Django secret key
- `DATABASE_PASSWORD` - PostgreSQL password
- `CREATE_SUPERUSER` - Initial admin credentials

### 2. Configure Environment

Edit `.env` and update:

```bash
# Required
SERVICE_HOSTNAME=errors.your-domain.com
PRIVATESUBNET=252  # Unique subnet ID (1-254)

# SMTP (for notifications)
EMAIL_HOST=smtp.your-domain.com
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
```

### 3. Deploy

**With Traefik (recommended):**
```bash
docker compose -f docker-compose.traefik.yml up -d
```

**Standalone (without reverse proxy):**
```bash
docker compose up -d
```

**Local Development (port 8000 exposed):**
```bash
docker compose -f docker-compose.development.yml up -d
```

### 4. Access

Open `https://errors.your-domain.com` and login with the credentials from `.env`:
- Email: `admin@example.com` (or your configured email)
- Password: (shown during secret generation)

**Important:** Remove `CREATE_SUPERUSER` from `.env` after first login.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Traefik Proxy                        │
│                 (HTTPS/Let's Encrypt)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Bugsink Server                         │
│               (Error Processing)                        │
│                                                         │
│  - Event ingestion (Sentry protocol)                    │
│  - Issue grouping & deduplication                       │
│  - Email notifications                                  │
│  - Web UI                                               │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              PostgreSQL 18 Database                     │
│           (SSD/NVMe performance tuning)                 │
└─────────────────────────────────────────────────────────┘
```

## Compose Files

| File | Description | Use Case |
|------|-------------|----------|
| `docker-compose.traefik.yml` | With Traefik labels and dynamic naming | Production with Traefik proxy |
| `docker-compose.yml` | Standalone with static naming | Production with custom proxy |
| `docker-compose.development.yml` | With exposed port 8000 | Local development |

## SDK Integration

Bugsink is compatible with Sentry SDKs. Example DSN format:

```
https://<project-key>@errors.your-domain.com/<project-id>
```

### Python Example

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://abc123@errors.your-domain.com/1",
    send_default_pii=True,      # Safe for self-hosted
    traces_sample_rate=0,        # Bugsink doesn't support traces
    environment="production",
)
```

### JavaScript Example

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
    dsn: "https://abc123@errors.your-domain.com/1",
    sendDefaultPii: true,
    tracesSampleRate: 0,
    environment: "production",
});
```

See [docs/SENTRY-SDK-COMPLETE-REFERENCE.md](docs/SENTRY-SDK-COMPLETE-REFERENCE.md) for all languages and frameworks.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_HOSTNAME` | - | Public hostname (DNS must resolve) |
| `SECRET_KEY` | - | Django secret key (generate with openssl) |
| `DATABASE_PASSWORD` | - | PostgreSQL password |
| `PRIVATESUBNET` | `254` | Unique subnet ID (1-254) |
| `PROXY_NETWORK` | `traefik` | External Traefik network name |

### User Registration

| Value | Description |
|-------|-------------|
| `CB_ANYBODY` | Anyone can sign up (dangerous!) |
| `CB_MEMBERS` | Existing users can invite |
| `CB_ADMINS` | Only admins can invite (default) |
| `CB_NOBODY` | Registration disabled |

### Rate Limits (per project)

| Instance Size | Projects | Events/5min | Events/hour |
|---------------|----------|-------------|-------------|
| Small | 1-10 | 1000 | 5000 |
| Medium | 10-50 | 2500 | 15000 |
| Large | 50-200 | 2500 | 15000 |
| XLarge | 200+ | 1500 | 10000 |

See [docs/BUGSINK-CONFIGURATION.md](docs/BUGSINK-CONFIGURATION.md) for complete configuration reference.

## Operations

### View Logs

```bash
# All services
docker compose logs -f

# Bugsink only
docker compose logs -f bugsink-server

# Database only
docker compose logs -f database-server
```

### Backup Database

```bash
docker compose exec database-server pg_dump -U bugsink bugsink > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker compose exec -T database-server psql -U bugsink bugsink
```

### Update

```bash
docker compose pull
docker compose up -d
```

## Directory Structure

```
.
├── docker-compose.yml              # Standalone deployment
├── docker-compose.traefik.yml      # Traefik deployment
├── docker-compose.development.yml  # Local development
├── .env.example                # Configuration template
├── .env                        # Local configuration (git-ignored)
├── docs/
│   ├── BUGSINK-CONFIGURATION.md
│   ├── BUGSINK-QUICKSTART.md
│   ├── BUGSINK-SDK-CONFIGURATION.md
│   ├── SENTRY-SDK-INTEGRATION.md
│   └── SENTRY-SDK-COMPLETE-REFERENCE.md
├── tools/
│   ├── Dockerfile              # Tools container
│   ├── run.cmd                 # Windows launcher
│   ├── run.sh                  # Linux/macOS launcher
│   └── run.ps1                 # PowerShell launcher
└── scripts/
    └── generate-secrets.sh     # Secret generation script
```

## Documentation

- [Quick Start Guide](docs/BUGSINK-QUICKSTART.md)
- [Configuration Reference](docs/BUGSINK-CONFIGURATION.md)
- [SDK Configuration](docs/BUGSINK-SDK-CONFIGURATION.md)
- [Sentry SDK Integration](docs/SENTRY-SDK-INTEGRATION.md)
- [Complete SDK Reference](docs/SENTRY-SDK-COMPLETE-REFERENCE.md)

## License

MIT. See [LICENSE](LICENSE) for details.
