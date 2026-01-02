# ==============================================================================
# Error Observability Tools Container
# ==============================================================================
# Lightweight container for running setup and maintenance scripts
#
# Usage:
#   ./run.sh generate-secrets    # Generate .env from .env.example
#   ./run.ps1 -Script generate-secrets
#
# ==============================================================================

FROM ubuntu:24.04

LABEL maintainer="DevOps Team"
LABEL description="Error Observability setup and maintenance tools"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install only required tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    openssl \
    sed \
    coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create working directories
WORKDIR /app
RUN mkdir -p /app/scripts /app/config

# Copy scripts
COPY ../scripts/ /app/scripts/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Default command shows help
CMD ["bash", "-c", "echo 'Error Observability Tools Container'; echo ''; echo 'Available scripts:'; ls -1 /app/scripts/*.sh 2>/dev/null | xargs -I{} basename {} || echo 'No scripts found'"]
