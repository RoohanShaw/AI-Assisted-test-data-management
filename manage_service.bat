@echo off
REM Service Management Utility for AI Test Data Generator
REM Usage: manage_service.bat [start|stop|restart|status|remove]

setlocal enabledelayedexpansion

set SERVICE_NAME=AITestDataGenerator
set COMMAND=%1

if "!COMMAND!"=="" (
    echo Usage: manage_service.bat [start^|stop^|restart^|status^|remove]
    echo.
    echo Examples:
    echo   manage_service.bat start       - Start the service
    echo   manage_service.bat stop        - Stop the service
    echo   manage_service.bat restart     - Restart the service
    echo   manage_service.bat status      - Check service status
    echo   manage_service.bat remove      - Remove the service
    echo.
    exit /b 1
)

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: This script must be run as Administrator
    exit /b 1
)

if /i "!COMMAND!"=="start" (
    echo Starting !SERVICE_NAME!...
    net start "!SERVICE_NAME!"
    if !ERRORLEVEL! equ 0 (
        echo ✓ Service started successfully
        echo API available at: http://localhost:9090/docs
    ) else (
        echo ✗ Failed to start service
        exit /b 1
    )
) else if /i "!COMMAND!"=="stop" (
    echo Stopping !SERVICE_NAME!...
    net stop "!SERVICE_NAME!"
    if !ERRORLEVEL! equ 0 (
        echo ✓ Service stopped successfully
    ) else (
        echo ✗ Failed to stop service
        exit /b 1
    )
) else if /i "!COMMAND!"=="restart" (
    echo Restarting !SERVICE_NAME!...
    net stop "!SERVICE_NAME!" >nul 2>&1
    timeout /t 2 /nobreak
    net start "!SERVICE_NAME!"
    if !ERRORLEVEL! equ 0 (
        echo ✓ Service restarted successfully
        echo API available at: http://localhost:9090/docs
    ) else (
        echo ✗ Failed to restart service
        exit /b 1
    )
) else if /i "!COMMAND!"=="status" (
    echo Checking !SERVICE_NAME! status...
    sc query "!SERVICE_NAME!"
    echo.
    net start | find /i "!SERVICE_NAME!" >nul
    if !ERRORLEVEL! equ 0 (
        echo Service Status: RUNNING ✓
        echo.
        echo.
        echo API Health Check:
        echo   Health Endpoint: http://127.0.0.1:9090/api/v1/health
        echo   Swagger UI:      http://127.0.0.1:9090/docs
        echo   Open the health endpoint in your browser or Postman to verify the service is running.
        echo.
    ) else (
        echo Service Status: STOPPED
    )
) else if /i "!COMMAND!"=="remove" (
    echo WARNING: This will remove the service!
    echo.
    set /p confirm="Continue? (y/n): "
    if /i "!confirm!"=="y" (
        echo Stopping service...
        net stop "!SERVICE_NAME!" >nul 2>&1
        
        echo Removing service...
        set NSSM_PATH=%~dp0nssm.exe
        if exist "!NSSM_PATH!" (
            "!NSSM_PATH!" remove "!SERVICE_NAME!" confirm
        ) else (
            sc delete "!SERVICE_NAME!"
        )
        
        echo ✓ Service removed
    )
) else (
    echo Unknown command: !COMMAND!
    echo Valid commands: start, stop, restart, status, remove
    exit /b 1
)

pause
