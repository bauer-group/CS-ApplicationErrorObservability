#!/bin/bash
# ==============================================================================
# Generate Secrets for Error Observability (Bugsink)
# ==============================================================================
# This script generates secure random values for all secrets and creates
# a .env file from .env.example
#
# Generated secrets:
#   - SECRET_KEY: Django secret key (base64, 50 bytes)
#   - DATABASE_PASSWORD: PostgreSQL password (alphanumeric, 32 chars)
#   - CREATE_SUPERUSER: Admin credentials with random password
#   - EMAIL_HOST_PASSWORD: SMTP password placeholder
#
# Usage:
#   ./generate-secrets.sh              # Interactive mode
#   ./generate-secrets.sh --force      # Overwrite existing .env
#   ./generate-secrets.sh --dry-run    # Show what would be generated
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_EXAMPLE="${PROJECT_DIR}/.env.example"
ENV_FILE="${PROJECT_DIR}/.env"

# Parse arguments
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force, -f     Overwrite existing .env file"
            echo "  --dry-run, -n   Show what would be generated without creating files"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate a secure random string (base64)
generate_secret_key() {
    openssl rand -base64 50 | tr -d '\n'
}

# Generate a secure alphanumeric password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

# Generate admin password (readable but secure)
generate_admin_password() {
    # 24 characters, alphanumeric
    openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24
}

# ==============================================================================
# Pre-flight Checks
# ==============================================================================

echo ""
echo "=============================================="
echo " Error Observability - Secret Generator"
echo "=============================================="
echo ""

# Check if .env.example exists
if [[ ! -f "$ENV_EXAMPLE" ]]; then
    log_error ".env.example not found at: $ENV_EXAMPLE"
    exit 1
fi

# Check if .env already exists
if [[ -f "$ENV_FILE" ]] && [[ "$FORCE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
    log_warning ".env file already exists!"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Aborted. Use --force to skip this prompt."
        exit 0
    fi
fi

# ==============================================================================
# Generate Secrets
# ==============================================================================

log_info "Generating secure secrets..."
echo ""

# Generate all secrets
SECRET_KEY=$(generate_secret_key)
DATABASE_PASSWORD=$(generate_password 32)
ADMIN_PASSWORD=$(generate_admin_password)

# Display generated values
echo "Generated values:"
echo "  SECRET_KEY:        ${SECRET_KEY:0:20}... (truncated)"
echo "  DATABASE_PASSWORD: ${DATABASE_PASSWORD:0:8}... (truncated)"
echo "  ADMIN_PASSWORD:    ${ADMIN_PASSWORD:0:8}... (truncated)"
echo ""

# ==============================================================================
# Create .env File
# ==============================================================================

if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Dry run mode - no files will be created"
    echo ""
    echo "Would create .env with:"
    echo "  SECRET_KEY=<generated>"
    echo "  DATABASE_PASSWORD=<generated>"
    echo "  CREATE_SUPERUSER=admin@example.com:<generated>"
    exit 0
fi

log_info "Creating .env file from .env.example..."

# Copy example to .env
cp "$ENV_EXAMPLE" "$ENV_FILE"

# Replace placeholder values with generated secrets
# SECRET_KEY
sed -i "s|SECRET_KEY=GENERATE_WITH_openssl_rand_base64_50|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE"

# DATABASE_PASSWORD (appears in multiple places)
sed -i "s|DATABASE_PASSWORD=CHANGE_ME_SECURE_PASSWORD|DATABASE_PASSWORD=${DATABASE_PASSWORD}|g" "$ENV_FILE"

# CREATE_SUPERUSER
sed -i "s|CREATE_SUPERUSER=admin@example.com:CHANGE_ME_SECURE_PASSWORD|CREATE_SUPERUSER=admin@example.com:${ADMIN_PASSWORD}|g" "$ENV_FILE"

# ==============================================================================
# Summary
# ==============================================================================

echo ""
log_success ".env file created successfully!"
echo ""
echo "=============================================="
echo " IMPORTANT: Save these credentials!"
echo "=============================================="
echo ""
echo "  Admin Login:"
echo "    Email:    admin@example.com"
echo "    Password: ${ADMIN_PASSWORD}"
echo ""
echo "  Database Password: ${DATABASE_PASSWORD}"
echo ""
echo "=============================================="
echo ""
log_warning "Next steps:"
echo "  1. Update SERVICE_HOSTNAME in .env"
echo "  2. Update EMAIL_HOST settings if needed"
echo "  3. Run: docker compose up -d"
echo "  4. After first login, remove CREATE_SUPERUSER from .env"
echo ""
log_info "Credentials are also stored in .env file"
echo ""
