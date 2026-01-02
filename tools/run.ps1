<#
.SYNOPSIS
    Error Observability Tools Runner (PowerShell)

.DESCRIPTION
    Runs scripts in a Docker container with all required tools for
    Error Observability (Bugsink) setup and maintenance.

.PARAMETER Script
    The name of the script to run (without .sh extension)

.PARAMETER Build
    Rebuild the Docker image before running the script

.PARAMETER List
    List all available scripts

.EXAMPLE
    .\run.ps1 -Script generate-secrets
    Runs the generate-secrets script

.EXAMPLE
    .\run.ps1 -Build -Script generate-secrets
    Rebuilds the image and runs the script

.EXAMPLE
    .\run.ps1 -List
    Lists all available scripts

.NOTES
    Requires Docker Desktop for Windows
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Script,

    [Parameter()]
    [switch]$Build,

    [Parameter()]
    [switch]$List
)

# Configuration
$ScriptDir = $PSScriptRoot
$ProjectDir = Split-Path -Parent $ScriptDir
$ImageName = "error-observability-tools"
$ContainerName = "error-observability-tools-runner"

# Colors
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARNING] $args" -ForegroundColor Yellow }
function Write-Err { Write-Host "[ERROR] $args" -ForegroundColor Red }

# List scripts
if ($List) {
    Write-Host "Available scripts:" -ForegroundColor Cyan
    Get-ChildItem -Path "$ProjectDir\scripts\*.sh" -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host "  $($_.BaseName)" }
    exit 0
}

# Validate script parameter
if (-not $Script) {
    Write-Err "No script name provided"
    Write-Host "Usage: .\run.ps1 -Script <script-name>"
    Write-Host "Run '.\run.ps1 -List' to see available scripts"
    exit 1
}

# Check if script exists
$ScriptPath = Join-Path $ProjectDir "scripts\$Script.sh"
if (-not (Test-Path $ScriptPath)) {
    Write-Err "Script not found: $Script.sh"
    Write-Host "Run '.\run.ps1 -List' to see available scripts"
    exit 1
}

# Check if Docker is running
try {
    $null = docker info 2>&1
}
catch {
    Write-Err "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check if image exists
$ImageExists = docker image inspect $ImageName 2>&1 | Out-Null; $?

# Build image if requested or if it doesn't exist
if ($Build -or -not $ImageExists) {
    Write-Info "Building Docker image..."

    $DockerfilePath = Join-Path $ScriptDir "Dockerfile"
    docker build -t $ImageName -f $DockerfilePath $ProjectDir

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to build Docker image"
        exit 1
    }

    Write-Success "Image built successfully"
}

# Convert Windows path to Docker-compatible path
$DockerProjectDir = $ProjectDir -replace '\\', '/' -replace '^([A-Za-z]):', '/$1'
$DockerProjectDir = $DockerProjectDir.ToLower()

# Run the script in container
Write-Info "Running $Script..."
Write-Host ""

docker run --rm -it `
    --name $ContainerName `
    -v "${ProjectDir}:/app/project" `
    -w /app/project `
    $ImageName `
    bash "/app/project/scripts/$Script.sh"

exit $LASTEXITCODE
