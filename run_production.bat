@echo off
REM ============================================================================
REM Production Runner - Multi-Account Order Processing
REM ============================================================================
REM This batch file runs the order processing system in PRODUCTION mode.
REM It processes orders from all active Bol.com accounts (Jean & Trivium).
REM
REM Usage: Double-click this file or run: run_production.bat
REM ============================================================================

echo.
echo ============================================================================
echo PRODUCTION MODE - Multi-Account Order Processing
echo ============================================================================
echo.
echo WARNING: This will process REAL orders from Bol.com!
echo.
echo Press Ctrl+C to cancel, or
pause

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    echo.
    pause
    exit /b 1
)

REM Run the production script
echo.
echo Starting production processing...
echo.
python run_production.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: Processing failed with errors
    echo ============================================================================
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================================
    echo Processing completed successfully
    echo ============================================================================
    echo.
    pause
    exit /b 0
)

