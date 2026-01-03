# =============================================================================
# Bugsink Error Observability - Custom Build
# Extended with Jira Cloud and GitHub Issues messaging backends
# =============================================================================
#
# This Dockerfile extends the official Bugsink image with custom messaging
# backends for Jira Cloud and GitHub Issues integration.
#
# Usage:
#   docker build -t bugsink-enhanced:latest .
#   docker-compose up -d
#
# =============================================================================

ARG BUGSINK_VERSION=2
FROM bugsink/bugsink:${BUGSINK_VERSION}

# Re-declare ARG after FROM to use it in labels
ARG BUGSINK_VERSION

# =============================================================================
# Custom Labels
# =============================================================================

# Metadata
LABEL vendor="BAUER GROUP"
LABEL maintainer="Karl Bauer <karl.bauer@bauer-group.com>"

# Opencontainers Metadata
LABEL org.opencontainers.image.title="ApplicationErrorObservability"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="BAUER GROUP"
LABEL org.opencontainers.image.authors="Karl Bauer <karl.bauer@bauer-group.com>"
LABEL org.opencontainers.image.source="https://github.com/bauer-group/CS-ApplicationErrorObservability"
LABEL org.opencontainers.image.url="https://github.com/bauer-group/CS-ApplicationErrorObservability"
LABEL org.opencontainers.image.documentation="https://github.com/bauer-group/CS-ApplicationErrorObservability#readme"
LABEL org.opencontainers.image.description="Bugsink Error Tracking - BAUER GROUP Edition"
LABEL org.opencontainers.image.version="0.0.0"

# Extended Labels
LABEL org.opencontainers.image.base.name="bugsink/bugsink:${BUGSINK_VERSION}"
LABEL com.bauer-group.bugsink.version="${BUGSINK_VERSION}"
LABEL com.bauer-group.features="jira-cloud,github-issues"

# =============================================================================
# Copy Custom Messaging Backends
# =============================================================================
# These backends extend Bugsink's alert system with Jira Cloud and GitHub Issues

# Debug: Show Bugsink structure before patching
RUN echo "=== Service Backends Directory ===" && \
    ls -la /app/alerts/service_backends/ && \
    echo "=== Models.py backend functions ===" && \
    grep -n "get_alert_service" /app/alerts/models.py | head -20

# Copy backend files to Bugsink's service_backends directory
COPY backends/jira_cloud.py /app/alerts/service_backends/jira_cloud.py
COPY backends/github_issues.py /app/alerts/service_backends/github_issues.py

# Copy the initialization patch script
COPY patches/register_backends.py /app/patches/register_backends.py

# =============================================================================
# Apply Backend Registration Patch
# =============================================================================
# This modifies the Bugsink backend registry to include our custom backends

RUN python /app/patches/register_backends.py && \
    rm -rf /app/patches

# Note: PORT, healthcheck and other defaults are inherited from base image.
