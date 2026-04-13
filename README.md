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

### More Languages

Complete integration examples are available for **10 languages**:

| Language | Example |
|----------|---------|
| Python | [examples/python_example.py](examples/python_example.py) |
| Node.js | [examples/nodejs_example.js](examples/nodejs_example.js) |
| TypeScript | [examples/typescript_example.ts](examples/typescript_example.ts) |
| Java | [examples/JavaExample.java](examples/JavaExample.java) |
| C# / .NET | [examples/DotNetExample.cs](examples/DotNetExample.cs) |
| Go | [examples/go_example.go](examples/go_example.go) |
| PHP | [examples/php_example.php](examples/php_example.php) |
| Ruby | [examples/ruby_example.rb](examples/ruby_example.rb) |
| Rust | [examples/rust_example.rs](examples/rust_example.rs) |
| C / C++ | [examples/cpp_example.cpp](examples/cpp_example.cpp) |

Each example includes:

- Full SDK initialization with configuration
- User context and breadcrumbs
- Error capturing and custom messages
- Performance monitoring (transactions/spans)
- Framework-specific integrations

See [docs/CLIENT-SDK-EXAMPLES.md](docs/CLIENT-SDK-EXAMPLES.md) for the complete integration guide.

### Automated Integration (Client-Kit)

Use the Client-Kit for quick, automated SDK integration:

```bash
# In your project directory
/path/to/client-kit/install.sh --dsn "https://key@errors.your-domain.com/1"
```

The installer will:

1. Detect your project language automatically
2. Install the SDK dependencies
3. Create a minimal configuration file
4. Add DSN to your `.env` file

**Three modes available:**

| Mode          | Command                          | Description              |
|---------------|----------------------------------|--------------------------|
| New Setup     | `./install.sh`                   | Full installation        |
| Update DSN    | `./install.sh --update-dsn`      | Change endpoint URL only |
| Update Client | `./install.sh --update-client`   | Refresh templates        |

See [client-kit/README.md](client-kit/README.md) for detailed documentation.

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
├── .env.example                    # Configuration template
├── .env                            # Local configuration (git-ignored)
├── docs/
│   ├── BUGSINK-CONFIGURATION.md
│   ├── BUGSINK-QUICKSTART.md
│   ├── BUGSINK-SDK-CONFIGURATION.md
│   ├── CLIENT-SDK-EXAMPLES.md      # SDK integration guide
│   ├── SENTRY-SDK-INTEGRATION.md
│   └── SENTRY-SDK-COMPLETE-REFERENCE.md
├── client-kit/                     # SDK Integration Tool
│   ├── install.py                  # Main installer (Python)
│   ├── install.sh                  # Shell wrapper
│   ├── install.ps1                 # PowerShell wrapper
│   ├── install.cmd                 # Windows batch wrapper
│   ├── templates/                  # Minimal integration templates
│   │   ├── python/
│   │   ├── nodejs/
│   │   ├── typescript/
│   │   ├── java/
│   │   ├── dotnet/
│   │   ├── go/
│   │   ├── php/
│   │   └── ruby/
│   └── README.md
├── examples/                       # Full SDK examples (reference)
│   ├── python_example.py
│   ├── nodejs_example.js
│   ├── typescript_example.ts
│   ├── JavaExample.java
│   ├── DotNetExample.cs
│   ├── go_example.go
│   ├── php_example.php
│   ├── ruby_example.rb
│   ├── rust_example.rs
│   └── cpp_example.cpp
├── tools/
│   ├── Dockerfile              # Tools container
│   ├── run.cmd                 # Windows launcher
│   ├── run.sh                  # Linux/macOS launcher
│   └── run.ps1                 # PowerShell launcher
└── scripts/
    └── generate-secrets.sh     # Secret generation script
```

## Bugsink Compatibility

This table shows which versions of this project are compatible with which Bugsink base versions. Always check for breaking changes before upgrading.

| Release | Bugsink Version | Breaking Changes | Notes |
| ------- | --------------- | ---------------- | ----- |
| **0.12.0+** | **2.1.x** | Yes | SSRF protection via `BaseWebhookBackend`, `webhook_security` module required. All custom backends updated. New settings: `ALERTS_WEBHOOK_*`, `MAX_EVENT_AGE_DAYS`, `MAX_STORED_FILE_*`, proxy headers. |
| 0.9.0 – 0.11.2 | 2.0.12 – 2.0.x | No | Initial stable release. Custom backends use direct `requests.post()`. |
| 0.1.0 – 0.8.x | 2.0.0 – 2.0.11 | No | Early development. Manual view/template patching required. |

### Upgrade Guide: 2.0.x → 2.1.x

When upgrading Bugsink from 2.0.x to 2.1.x, the following changes apply:

1. **Custom backends** now inherit from `BaseWebhookBackend` (Teams, Generic Webhook) or use `validate_webhook_url()` (Jira, GitHub, PagerDuty) for SSRF protection.
2. **New environment variables** are available in `.env` — see [Webhook Security](docs/BUGSINK-CONFIGURATION.md#webhook-security), [Data Retention](docs/BUGSINK-CONFIGURATION.md#data-retention), and [Proxy Headers](docs/BUGSINK-CONFIGURATION.md#proxy-headers).
3. **Non-global IPs are blocked by default** (`ALERTS_WEBHOOK_DENY_NON_GLOBAL=true`). If your notification targets are on internal networks, set this to `false` or add them to `ALERTS_WEBHOOK_ALLOW_LIST`.
4. **Database migrations** run automatically on container start — no manual action required.

### Key Bugsink Changes per Version

| Bugsink Version | Key Changes |
| --------------- | ----------- |
| 2.1.2 | Storage capacity management (file count + byte caps) |
| 2.1.1 | Security fix for upload checksums, sourcemap null handling |
| 2.1.0 | SSRF protection (`BaseWebhookBackend`, `webhook_security`), object storage, `vacuum` command, `MAX_EVENT_AGE_DAYS`, proxy header settings |
| 2.0.12 | Last version without SSRF protection module |

## Documentation

- [Quick Start Guide](docs/BUGSINK-QUICKSTART.md)
- [Configuration Reference](docs/BUGSINK-CONFIGURATION.md)
- [SDK Configuration](docs/BUGSINK-SDK-CONFIGURATION.md)
- [Client SDK Examples](docs/CLIENT-SDK-EXAMPLES.md) - Integration examples for 10 languages
- [Client-Kit](client-kit/README.md) - Automated SDK integration tool
- [Sentry SDK Integration](docs/SENTRY-SDK-INTEGRATION.md)
- [Complete SDK Reference](docs/SENTRY-SDK-COMPLETE-REFERENCE.md)
- [Notification Backends](docs/NOTIFICATION_BACKENDS.md) - Jira, GitHub, Teams, PagerDuty, Webhook

## License

See [LICENSE](LICENSE) for details.
