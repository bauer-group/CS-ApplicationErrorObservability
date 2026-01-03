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
LABEL com.bauer-group.features="jira-cloud,github-issues,microsoft-teams,pagerduty,webhook"

# =============================================================================
# Copy Custom Messaging Backends
# =============================================================================
# These backends extend Bugsink's alert system with Jira Cloud and GitHub Issues
# Note: Base image uses USER bugsink, we need root to modify site-packages

USER root

# Bugsink is installed as a Python package in site-packages
ENV BUGSINK_SITE_PACKAGES=/usr/local/lib/python3.12/site-packages

# Copy all backend files to Bugsink's service_backends directory
COPY backends/*.py ${BUGSINK_SITE_PACKAGES}/alerts/service_backends/

# Copy patch scripts
COPY patches/*.py /tmp/patches/

# =============================================================================
# Apply Patches
# =============================================================================
# 1. Register custom backends in alerts/models.py
# 2. Patch views to use dynamic ConfigForm loading based on backend kind
# 3. Patch template to reload form when backend type changes

RUN python /tmp/patches/register_backends.py && \
    python /tmp/patches/patch_views.py && \
    python /tmp/patches/patch_template.py && \
    rm -rf /tmp/patches

# Switch back to bugsink user for runtime security
USER bugsink

# Note: PORT, healthcheck and other defaults are inherited from base image.
