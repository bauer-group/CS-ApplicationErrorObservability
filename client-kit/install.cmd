@echo off
REM Error Observability Client Kit - Windows Batch Wrapper
REM ======================================================

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "INSTALLER=%SCRIPT_DIR%install.py"

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
    goto :run
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python3"
    goto :run
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py"
    goto :run
)

echo Error: Python 3 is required but not installed.
echo Please install Python from https://www.python.org/downloads/
exit /b 1

:run
echo.
echo ==========================================
echo   Error Observability - Client Kit
echo ==========================================
echo.

%PYTHON_CMD% "%INSTALLER%" %*
