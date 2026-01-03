@echo off
REM ============================================================================
REM Scheduled Order Processor - Multi-Account Processing
REM ============================================================================
REM This script processes orders at scheduled times (08:00, 15:01, etc.)
REM automatically for both Jean and Trivium accounts.
REM
REM Usage: Double-click this file or run: run_realtime_monitor.bat
REM Press Ctrl+C to stop the processor
REM ============================================================================

echo.
echo ============================================================================
echo SCHEDULED ORDER PROCESSOR - Multi-Account Processing
echo ============================================================================
echo.
echo This will process orders at scheduled times (08:00, 15:01, etc.)
echo.
echo IMPORTANT:
echo   - Runs in PRODUCTION mode (real orders!)
echo   - Processes both Jean and Trivium accounts automatically
echo   - Runs ONLY at scheduled times (no per-minute checking)
echo   - Configure times in system_config.json
echo   - Press Ctrl+C to stop the processor
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

REM Run the scheduled processor script
python run_realtime_monitor.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: Processor stopped with errors
    echo ============================================================================
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================================
    echo Processor stopped normally
    echo ============================================================================
    echo.
    pause
    exit /b 0
)

