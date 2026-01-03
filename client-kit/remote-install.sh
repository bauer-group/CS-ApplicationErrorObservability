#!/bin/bash
#
# Error Observability Client-Kit - Remote Installer
# ==================================================
# Execute directly from GitHub without cloning the repo.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/YOUR_ORG/ApplicationErrorObservability/main/client-kit/remote-install.sh | bash
#   curl -sSL <URL> | bash -s -- --dsn "https://..."
#   wget -qO- <URL> | bash -s -- --dsn "https://..."
#

set -e

# Configuration - UPDATE THIS URL TO YOUR REPO
REPO_RAW_URL="${CLIENT_KIT_REPO_URL:-https://raw.githubusercontent.com/YOUR_ORG/ApplicationErrorObservability/main/client-kit}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  Error Observability - Client Kit (Remote)${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Check for required tools
check_requirements() {
    # Check for curl or wget
    if command -v curl &> /dev/null; then
        DOWNLOAD_CMD="curl -sSL"
    elif command -v wget &> /dev/null; then
        DOWNLOAD_CMD="wget -qO-"
    else
        echo -e "${RED}Error: curl or wget is required${NC}"
        exit 1
    fi

    # Check for Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        # Verify it's Python 3
        if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}Error: Python 3.7+ is required${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Error: Python 3 is required${NC}"
        echo "Install: https://www.python.org/downloads/"
        exit 1
    fi

    echo -e "${GREEN}✓ Found Python: $($PYTHON_CMD --version)${NC}"
}

# Create temporary directory
setup_temp_dir() {
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    echo -e "${CYAN}Downloading client-kit...${NC}"
}

# Download files
download_files() {
    # Download main installer
    $DOWNLOAD_CMD "$REPO_RAW_URL/install.py" > "$TEMP_DIR/install.py"

    # Create templates directory
    mkdir -p "$TEMP_DIR/templates"

    # Download templates for each language
    for lang in python nodejs typescript java dotnet go php ruby; do
        mkdir -p "$TEMP_DIR/templates/$lang"

        case $lang in
            python)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/python/sentry_config.py" > "$TEMP_DIR/templates/python/sentry_config.py" 2>/dev/null || true
                ;;
            nodejs)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/nodejs/sentry.config.js" > "$TEMP_DIR/templates/nodejs/sentry.config.js" 2>/dev/null || true
                ;;
            typescript)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/typescript/sentry.config.ts" > "$TEMP_DIR/templates/typescript/sentry.config.ts" 2>/dev/null || true
                ;;
            java)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/java/SentryConfig.java" > "$TEMP_DIR/templates/java/SentryConfig.java" 2>/dev/null || true
                ;;
            dotnet)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/dotnet/SentryConfig.cs" > "$TEMP_DIR/templates/dotnet/SentryConfig.cs" 2>/dev/null || true
                ;;
            go)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/go/sentry.go" > "$TEMP_DIR/templates/go/sentry.go" 2>/dev/null || true
                ;;
            php)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/php/sentry.php" > "$TEMP_DIR/templates/php/sentry.php" 2>/dev/null || true
                ;;
            ruby)
                $DOWNLOAD_CMD "$REPO_RAW_URL/templates/ruby/sentry.rb" > "$TEMP_DIR/templates/ruby/sentry.rb" 2>/dev/null || true
                ;;
        esac
    done

    echo -e "${GREEN}✓ Downloaded successfully${NC}"
    echo ""
}

# Run installer
run_installer() {
    $PYTHON_CMD "$TEMP_DIR/install.py" "$@"
}

# Main
main() {
    check_requirements
    setup_temp_dir
    download_files
    run_installer "$@"
}

main "$@"
