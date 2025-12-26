@echo off
REM ============================================================================
REM Background Monitor Starter
REM This script starts the monitor in the background and saves the PID
REM ============================================================================

REM Get the directory where this script is located
cd /d "%~dp0"

REM Start Python script in background and capture PID
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do set LAST_PID=%%a

REM Start the monitor
start /B "" python run_realtime_monitor.py

REM Wait a moment for process to start
timeout /t 2 /nobreak >nul

REM Find the new Python process running our script
for /f "tokens=2" %%a in ('wmic process where "name='python.exe'" get ProcessId^,CommandLine /format:csv ^| find "run_realtime_monitor.py"') do (
    echo %%a > monitor.pid
    exit /b 0
)

REM If we couldn't find it, try a different method
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    if %%a neq %LAST_PID% (
        echo %%a > monitor.pid
        exit /b 0
    )
)

exit /b 1

