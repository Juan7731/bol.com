@echo off
REM ============================================================================
REM Deploy Codebase to SFTP Server
REM ============================================================================
REM This script uploads all necessary files to the SFTP server.
REM
REM Usage: Double-click this file or run: deploy_to_sftp.bat
REM ============================================================================

echo.
echo ============================================================================
echo DEPLOY CODEBASE TO SFTP SERVER
echo ============================================================================
echo.
echo This will upload all Python files and configuration to the SFTP server.
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

REM Run the deployment script
echo.
echo Starting deployment...
echo.
python deploy_to_sftp.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: Deployment failed
    echo ============================================================================
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================================
    echo Deployment completed successfully
    echo ============================================================================
    echo.
    pause
    exit /b 0
)

