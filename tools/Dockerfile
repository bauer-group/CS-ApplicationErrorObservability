# =============================================================================
# Error Observability Tools Container
# All tools needed to run setup scripts on any platform
# =============================================================================

FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install all required tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core utilities
    bash \
    coreutils \
    grep \
    sed \
    # OpenSSL for secret generation
    openssl \
    # Useful extras
    curl \
    jq \
    ca-certificates \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set bash as default shell
SHELL ["/bin/bash", "-c"]

# Working directory (will be mounted from host)
WORKDIR /workspace

# Default command: interactive bash
CMD ["/bin/bash"]
