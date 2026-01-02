@echo off
REM ==============================================================================
REM Error Observability Tools Runner (Windows CMD)
REM ==============================================================================
REM Runs scripts in a Docker container with all required tools
REM
REM Usage:
REM   run.cmd <script-name>           Run a script
REM   run.cmd --build <script-name>   Rebuild container and run script
REM   run.cmd --list                  List available scripts
REM
REM Examples:
REM   run.cmd generate-secrets
REM   run.cmd --build generate-secrets
REM
REM ==============================================================================

setlocal enabledelayedexpansion

REM Configuration
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "IMAGE_NAME=error-observability-tools"
set "CONTAINER_NAME=error-observability-tools-runner"

REM Parse arguments
set "BUILD=false"
set "SCRIPT_NAME="

:parse_args
if "%~1"=="" goto :check_args
if /i "%~1"=="--build" (
    set "BUILD=true"
    shift
    goto :parse_args
)
if /i "%~1"=="-b" (
    set "BUILD=true"
    shift
    goto :parse_args
)
if /i "%~1"=="--list" (
    echo Available scripts:
    dir /b "%PROJECT_DIR%\scripts\*.sh" 2>nul
    exit /b 0
)
if /i "%~1"=="-l" (
    echo Available scripts:
    dir /b "%PROJECT_DIR%\scripts\*.sh" 2>nul
    exit /b 0
)
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if "%~1:~0,1%"=="-" (
    echo Error: Unknown option: %~1
    exit /b 1
)
set "SCRIPT_NAME=%~1"
shift
goto :parse_args

:check_args
if "%SCRIPT_NAME%"=="" (
    echo Error: No script name provided
    echo Usage: %~nx0 ^<script-name^>
    echo Run '%~nx0 --list' to see available scripts
    exit /b 1
)

REM Check if script exists
if not exist "%PROJECT_DIR%\scripts\%SCRIPT_NAME%.sh" (
    echo Error: Script not found: %SCRIPT_NAME%.sh
    echo Run '%~nx0 --list' to see available scripts
    exit /b 1
)

REM Build image if requested
if "%BUILD%"=="true" (
    echo Building Docker image...
    docker build -t %IMAGE_NAME% -f "%SCRIPT_DIR%Dockerfile" "%PROJECT_DIR%"
    if errorlevel 1 (
        echo Error: Failed to build Docker image
        exit /b 1
    )
    echo Image built successfully
)

REM Check if image exists, build if not
docker image inspect %IMAGE_NAME% >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t %IMAGE_NAME% -f "%SCRIPT_DIR%Dockerfile" "%PROJECT_DIR%"
    if errorlevel 1 (
        echo Error: Failed to build Docker image
        exit /b 1
    )
)

REM Run the script in container
echo Running %SCRIPT_NAME%...
echo.

docker run --rm -it ^
    --name %CONTAINER_NAME% ^
    -v "%PROJECT_DIR%:/app/project" ^
    -w /app/project ^
    %IMAGE_NAME% ^
    bash "/app/project/scripts/%SCRIPT_NAME%.sh"

exit /b %errorlevel%

:show_help
echo Usage: %~nx0 [OPTIONS] ^<script-name^>
echo.
echo Options:
echo   --build, -b    Rebuild the Docker image before running
echo   --list, -l     List available scripts
echo   --help, -h     Show this help message
echo.
echo Examples:
echo   %~nx0 generate-secrets
echo   %~nx0 --build generate-secrets
exit /b 0
