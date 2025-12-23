@echo off
REM ============================================================================
REM Real-Time Order Monitor - Multi-Account Processing
REM ============================================================================
REM This script monitors for new orders every minute and processes them
REM automatically for both Jean and Trivium accounts.
REM
REM Usage: Double-click this file or run: run_realtime_monitor.bat
REM Press Ctrl+C to stop the monitor
REM ============================================================================

echo.
echo ============================================================================
echo REAL-TIME ORDER MONITOR - Multi-Account Processing
echo ============================================================================
echo.
echo This will monitor for new orders every minute and process them automatically.
echo.
echo IMPORTANT:
echo   - Runs in PRODUCTION mode (real orders!)
echo   - Checks both Jean and Trivium accounts
echo   - Runs every 60 seconds continuously
echo   - Press Ctrl+C to stop the monitor
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

REM Show start time
echo.
echo Starting monitor at: %date% %time%
echo.

REM Run the real-time monitor script
python run_realtime_monitor.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: Monitor stopped with errors
    echo ============================================================================
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================================
    echo Monitor stopped normally
    echo ============================================================================
    echo.
    pause
    exit /b 0
)

