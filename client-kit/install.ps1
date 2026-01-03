<#
.SYNOPSIS
    Error Observability Client Kit - PowerShell Wrapper

.DESCRIPTION
    Cross-platform installer for Sentry SDK integration.

.PARAMETER Dsn
    Sentry/Bugsink DSN

.PARAMETER Environment
    Environment name (default: production)

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
    $args = @()

    if ($Dsn) {
        $args += "--dsn"
        $args += $Dsn
    }

    if ($Environment -and $Environment -ne "production") {
        $args += "--environment"
        $args += $Environment
    }

    if ($Release) {
        $args += "--release"
        $args += $Release
    }

    if ($UpdateDsn) {
        $args += "--update-dsn"
    }

    if ($UpdateClient) {
        $args += "--update-client"
    }

    if ($ProjectRoot) {
        $args += "--project-root"
        $args += $ProjectRoot
    }

    # Run installer
    if ($args.Count -gt 0) {
        & $pythonCmd $Installer @args
    }
    else {
        & $pythonCmd $Installer
    }
}

Main
