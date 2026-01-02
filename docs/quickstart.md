# Bugsink Quick Start Guide

Get Bugsink up and running in minutes with this step-by-step guide.

## Prerequisites

- Docker and Docker Compose installed
- A domain name pointing to your server
- Traefik reverse proxy configured with Let's Encrypt
- Access to an SMTP server (optional, but recommended)

## Installation Steps

### 1. Clone or Copy the Configuration

```bash
cd /opt/containers  # or your preferred location
mkdir bugsink && cd bugsink
# Copy docker-compose.yml and .env.example to this directory
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Generate Secrets

Generate a secure secret key:

```bash
openssl rand -base64 50
```

Generate a secure database password:

```bash
openssl rand -base64 32
```

### 4. Configure Required Settings

Edit `.env` and update the following **required** settings:

```ini
# Stack identification
STACK_NAME=bugsink_yourcompany_com

# Network (choose unique subnet to avoid conflicts)
PRIVATESUBNET=252

# Your domain
SERVICE_HOSTNAME=bugsink.yourcompany.com

# Traefik network name
PROXY_NETWORK=EDGEPROXY

# Application secret (paste generated value)
SECRET_KEY=your-generated-secret-key-here

# Database password (paste generated value)
DATABASE_PASSWORD=your-generated-password-here

# Initial admin account
CREATE_SUPERUSER=admin@yourcompany.com:YourSecurePassword123!
```

### 5. Configure Email (Recommended)

For password resets and notifications to work:

```ini
EMAIL_HOST=smtp.yourcompany.com
EMAIL_PORT=587
EMAIL_HOST_USER=bugsink@yourcompany.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=Bugsink <bugsink@yourcompany.com>
```

### 6. Start the Services

```bash
docker compose up -d
```

### 7. Verify Deployment

Check container status:

```bash
docker compose ps
```

Both containers should show as "healthy":

```
NAME                      STATUS
bugsink_SERVER            Up (healthy)
bugsink_DATABASE          Up (healthy)
```

View logs if needed:

```bash
docker compose logs -f bugsink-server
```

### 8. Access Bugsink

Open your browser and navigate to:

```
https://bugsink.yourcompany.com
```

Log in with the credentials you set in `CREATE_SUPERUSER`.

### 9. Security: Remove Initial Credentials

After confirming login works:

1. Edit `.env`
2. Remove or comment out the `CREATE_SUPERUSER` line
3. Restart:
   ```bash
   docker compose restart bugsink-server
   ```

## Post-Installation

### Create Your First Project

1. Log in to Bugsink
2. Click "Create Project"
3. Enter a project name
4. Copy the generated DSN

### Configure Your Application

Install the Sentry SDK for your language/framework and configure it with your DSN:

**Python:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
)
```

**JavaScript:**
```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
});
```

**See also:** [Sentry SDK Integration Guide](sentry-sdk-integration.md)

## Common Operations

### View Logs

```bash
# All services
docker compose logs -f

# Application only
docker compose logs -f bugsink-server

# Database only
docker compose logs -f database-server
```

### Restart Services

```bash
# All services
docker compose restart

# Application only
docker compose restart bugsink-server
```

### Update Bugsink

```bash
# Pull latest image
docker compose pull bugsink-server

# Recreate container
docker compose up -d bugsink-server
```

### Backup Database

```bash
docker compose exec database-server pg_dump -U bugsink bugsink > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
cat backup_20240101.sql | docker compose exec -T database-server psql -U bugsink bugsink
```

## Troubleshooting

### Container Won't Start

Check logs for errors:
```bash
docker compose logs bugsink-server
```

Common issues:
- Invalid `SECRET_KEY` format
- Database connection refused (database not ready)
- Invalid `CREATE_SUPERUSER` format (must be `email:password`)

### Can't Access Web Interface

1. Verify DNS resolves correctly:
   ```bash
   nslookup bugsink.yourcompany.com
   ```

2. Check Traefik routing:
   ```bash
   docker logs traefik 2>&1 | grep bugsink
   ```

3. Verify container is on proxy network:
   ```bash
   docker network inspect EDGEPROXY
   ```

### Email Not Working

1. Enable email logging:
   ```ini
   EMAIL_LOGGING=true
   ```

2. Restart and check logs:
   ```bash
   docker compose restart bugsink-server
   docker compose logs -f bugsink-server
   ```

3. Test SMTP connectivity:
   ```bash
   docker compose exec bugsink-server python -c "
   import smtplib
   s = smtplib.SMTP('smtp.yourcompany.com', 587)
   s.starttls()
   s.login('user', 'pass')
   print('SMTP OK')
   "
   ```

### Database Connection Issues

1. Check database health:
   ```bash
   docker compose exec database-server pg_isready -U bugsink
   ```

2. Verify password matches in both places:
   - `DATABASE_PASSWORD` in `.env`
   - Connection URL uses the same password

## Next Steps

- [Configuration Reference](configuration.md) - All available settings
- [Sentry SDK Integration](sentry-sdk-integration.md) - Connect your applications
