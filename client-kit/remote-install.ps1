<#
.SYNOPSIS
    Error Observability Client-Kit - Remote Installer (PowerShell)

.DESCRIPTION
    Execute directly from GitHub without cloning the repo.

.EXAMPLE
    # Run directly from URL:
    irm https://raw.githubusercontent.com/bauer-group/CS-ApplicationErrorObservability/main/client-kit/remote-install.ps1 | iex

    # Or with parameters (save first, then run):
    Invoke-WebRequest -Uri "<URL>" -OutFile install.ps1; .\install.ps1 -Dsn "https://..."

    # API Mode (automatic project creation):
    .\install.ps1 -ApiKey "..." -ApiUrl "https://errors.example.com"
    .\install.ps1 -ApiKey "..." -ApiUrl "..." -Team "MyTeam" -Project "MyApp"

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
    Only update the DSN

.PARAMETER UpdateClient
    Update client code from templates
#>

[CmdletBinding()]
param(
    [string]$Dsn,
    [string]$Environment = "production",
    [string]$Release,
    [string]$ApiKey,
    [string]$ApiUrl,
    [string]$Team,
    [string]$Project,
    [switch]$UpdateDsn,
    [switch]$UpdateClient
)

$ErrorActionPreference = "Stop"

# Configuration
$RepoRawUrl = if ($env:CLIENT_KIT_REPO_URL) { $env:CLIENT_KIT_REPO_URL } else { "https://raw.githubusercontent.com/bauer-group/CS-ApplicationErrorObservability/main/client-kit" }

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-PythonInstalled {
    $pythonCommands = @("python3", "python", "py")

    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $versionString = ($version -replace "Python ", "").Trim()
                $parts = $versionString.Split(".")
                $major = [int]$parts[0]
                $minor = [int]$parts[1]

                if ($major -ge 3 -and $minor -ge 7) {
                    Write-ColorOutput "Found Python $versionString" -Color Green
                    return $cmd
                }
            }
        }
        catch { }
    }

    Write-ColorOutput "Error: Python 3.7+ is required" -Color Red
    Write-Host "Install from: https://www.python.org/downloads/"
    exit 1
}

function Get-RemoteFile {
    param([string]$Url, [string]$Destination)

    try {
        Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Main {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  Error Observability - Client Kit (Remote)" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""

    # Check Python
    $pythonCmd = Test-PythonInstalled

    # Create temp directory
    $tempDir = Join-Path $env:TEMP "client-kit-$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    try {
        Write-ColorOutput "Downloading client-kit..." -Color Cyan

        # Download main installer
        Get-RemoteFile -Url "$RepoRawUrl/install.py" -Destination "$tempDir\install.py"

        # Create templates directory
        $templatesDir = Join-Path $tempDir "templates"
        New-Item -ItemType Directory -Path $templatesDir -Force | Out-Null

        # Download templates
        $languages = @{
            "python"     = "sentry_config.py"
            "nodejs"     = "sentry.config.js"
            "typescript" = "sentry.config.ts"
            "java"       = "SentryConfig.java"
            "dotnet"     = "SentryConfig.cs"
            "go"         = "sentry.go"
            "php"        = "sentry.php"
            "ruby"       = "sentry.rb"
        }

        foreach ($lang in $languages.Keys) {
            $langDir = Join-Path $templatesDir $lang
            New-Item -ItemType Directory -Path $langDir -Force | Out-Null

            $file = $languages[$lang]
            Get-RemoteFile -Url "$RepoRawUrl/templates/$lang/$file" -Destination "$langDir\$file" | Out-Null
        }

        Write-ColorOutput "Downloaded successfully" -Color Green
        Write-Host ""

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

        # Run installer
        $installerPath = Join-Path $tempDir "install.py"

        if ($installerArgs.Count -gt 0) {
            & $pythonCmd $installerPath @installerArgs
        }
        else {
            & $pythonCmd $installerPath
        }
    }
    finally {
        # Cleanup
        if (Test-Path $tempDir) {
            Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        }
    }
}

Main
