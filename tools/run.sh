#!/bin/bash
# ==============================================================================
# Error Observability Tools Runner (Linux/macOS)
# ==============================================================================
# Runs scripts in a Docker container with all required tools
#
# Usage:
#   ./run.sh <script-name>           # Run a script
#   ./run.sh --build <script-name>   # Rebuild container and run script
#   ./run.sh --list                  # List available scripts
#
# Examples:
#   ./run.sh generate-secrets
#   ./run.sh --build generate-secrets
#
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="error-observability-tools"
CONTAINER_NAME="error-observability-tools-runner"

# Parse arguments
BUILD=false
SCRIPT_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            BUILD=true
            shift
            ;;
        --list|-l)
            echo "Available scripts:"
            ls -1 "${PROJECT_DIR}/scripts/"*.sh 2>/dev/null | xargs -I{} basename {} .sh || echo "No scripts found"
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] <script-name>"
            echo ""
            echo "Options:"
            echo "  --build, -b    Rebuild the Docker image before running"
            echo "  --list, -l     List available scripts"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 generate-secrets"
            echo "  $0 --build generate-secrets"
            exit 0
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
        *)
            SCRIPT_NAME="$1"
            shift
            ;;
    esac
done

# Validate script name
if [[ -z "$SCRIPT_NAME" ]]; then
    echo -e "${RED}Error: No script name provided${NC}"
    echo "Usage: $0 <script-name>"
    echo "Run '$0 --list' to see available scripts"
    exit 1
fi

# Check if script exists
SCRIPT_PATH="${PROJECT_DIR}/scripts/${SCRIPT_NAME}.sh"
if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo -e "${RED}Error: Script not found: ${SCRIPT_NAME}.sh${NC}"
    echo "Run '$0 --list' to see available scripts"
    exit 1
fi

# Build image if requested or if it doesn't exist
if [[ "$BUILD" == "true" ]] || ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t "$IMAGE_NAME" -f "${SCRIPT_DIR}/Dockerfile" "$PROJECT_DIR"
    echo -e "${GREEN}Image built successfully${NC}"
fi

# Run the script in container
echo -e "${GREEN}Running ${SCRIPT_NAME}...${NC}"
echo ""

docker run --rm -it \
    --name "$CONTAINER_NAME" \
    -v "${PROJECT_DIR}:/app/project" \
    -w /app/project \
    "$IMAGE_NAME" \
    bash "/app/project/scripts/${SCRIPT_NAME}.sh" "$@"
