#!/bin/bash
#
# Error Observability Client Kit - Shell Wrapper
# ===============================================
# Cross-platform installer for Sentry SDK integration.
#
# Usage:
#   ./install.sh                     # Interactive mode
#   ./install.sh --dsn "https://..." # With DSN
#   curl -sSL <url>/install.sh | bash -s -- --dsn "..."
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/install.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        echo "Please install Python 3.7 or later."
        exit 1
    fi

    # Verify Python version
    VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    MAJOR=$(echo $VERSION | cut -d. -f1)
    MINOR=$(echo $VERSION | cut -d. -f2)

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 7 ]); then
        echo -e "${RED}Error: Python 3.7+ is required (found $VERSION)${NC}"
        exit 1
    fi

    echo -e "${GREEN}Found Python $VERSION${NC}"
}

# Download installer if running from URL
download_installer() {
    if [ ! -f "$INSTALLER" ]; then
        REPO_URL="https://raw.githubusercontent.com/your-org/ApplicationErrorObservability/main/client-kit"
        TEMP_DIR=$(mktemp -d)

        echo "Downloading client-kit..."

        # Download main installer
        curl -sSL "$REPO_URL/install.py" -o "$TEMP_DIR/install.py"

        # Download templates
        mkdir -p "$TEMP_DIR/templates"
        for lang in python nodejs typescript java dotnet go php ruby; do
            mkdir -p "$TEMP_DIR/templates/$lang"
            curl -sSL "$REPO_URL/templates/$lang/"* -o "$TEMP_DIR/templates/$lang/" 2>/dev/null || true
        done

        INSTALLER="$TEMP_DIR/install.py"
        SCRIPT_DIR="$TEMP_DIR"
    fi
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "  Error Observability - Client Kit"
    echo "=========================================="
    echo ""

    check_python

    # Run installer
    $PYTHON_CMD "$INSTALLER" "$@"
}

main "$@"
