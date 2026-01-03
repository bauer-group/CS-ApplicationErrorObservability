<#
.SYNOPSIS
    Error Observability Client Kit - PowerShell Wrapper

.DESCRIPTION
    Cross-platform installer for Sentry SDK integration.

.PARAMETER Dsn
    Sentry/Bugsink DSN

.PARAMETER Environment
    Environment name (default: production)

.PARAMETER ApiKey
    Bugsink API key for automatic project setup

.PARAMETER ApiUrl
    Bugsink server URL

.PARAMETER Team
    Team name for API mode

.PARAMETER Project
    Project name for API mode

.PARAMETER UpdateDsn
    Only update the DSN in existing configuration

.PARAMETER UpdateClient
    Update client code from templates

.EXAMPLE
    .\install.ps1
    # Interactive mode

.EXAMPLE
    .\install.ps1 -Dsn "https://key@host/1"
    # Install with DSN

.EXAMPLE
    .\install.ps1 -ApiKey "..." -ApiUrl "https://errors.example.com"
    # API mode with automatic project setup

.EXAMPLE
    .\install.ps1 -UpdateDsn -Dsn "https://key@host/1"
    # Update DSN only
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$Dsn,

    [Parameter()]
    [string]$Environment = "production",

    [Parameter()]
    [string]$Release,

    [Parameter()]
    [string]$ApiKey,

    [Parameter()]
    [string]$ApiUrl,

    [Parameter()]
    [string]$Team,

    [Parameter()]
    [string]$Project,

    [Parameter()]
    [switch]$UpdateDsn,

    [Parameter()]
    [switch]$UpdateClient,

    [Parameter()]
    [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $ScriptDir "install.py"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-PythonInstalled {
    $pythonCommands = @("python3", "python", "py")

    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $versionString = $version -replace "Python ", ""
                $parts = $versionString.Split(".")
                $major = [int]$parts[0]
                $minor = [int]$parts[1]

                if ($major -ge 3 -and $minor -ge 7) {
                    Write-ColorOutput "Found Python $versionString" -Color Green
                    return $cmd
                }
            }
        }
        catch {
            # Continue to next command
        }
    }

    Write-ColorOutput "Error: Python 3.7+ is required but not installed." -Color Red
    Write-Host "Please install Python from https://www.python.org/downloads/"
    exit 1
}

function Main {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  Error Observability - Client Kit" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""

    $pythonCmd = Test-PythonInstalled

    # Build arguments
    $installerArgs = @()

    if ($Dsn) {
        $installerArgs += "--dsn"
        $installerArgs += $Dsn
    }

    if ($Environment -and $Environment -ne "production") {
        $installerArgs += "--environment"
        $installerArgs += $Environment
    }

    if ($Release) {
        $installerArgs += "--release"
        $installerArgs += $Release
    }

    if ($ApiKey) {
        $installerArgs += "--api-key"
        $installerArgs += $ApiKey
    }

    if ($ApiUrl) {
        $installerArgs += "--api-url"
        $installerArgs += $ApiUrl
    }

    if ($Team) {
        $installerArgs += "--team"
        $installerArgs += $Team
    }

    if ($Project) {
        $installerArgs += "--project"
        $installerArgs += $Project
    }

    if ($UpdateDsn) {
        $installerArgs += "--update-dsn"
    }

    if ($UpdateClient) {
        $installerArgs += "--update-client"
    }

    if ($ProjectRoot) {
        $installerArgs += "--project-root"
        $installerArgs += $ProjectRoot
    }

    # Run installer
    if ($installerArgs.Count -gt 0) {
        & $pythonCmd $Installer @installerArgs
    }
    else {
        & $pythonCmd $Installer
    }
}

Main
