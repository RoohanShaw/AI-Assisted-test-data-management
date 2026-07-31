@echo off
REM Install AI Test Data Generator as Windows Service using NSSM
REM Usage: install_service.bat [SERVICE_NAME] [EXE_PATH]
REM Default: AITestDataGenerator, C:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe

setlocal enabledelayedexpansion

REM Configuration
set SERVICE_NAME=%1
if "!SERVICE_NAME!"=="" set SERVICE_NAME=AITestDataGenerator

set EXE_PATH=%2
if "!EXE_PATH!"=="" set EXE_PATH=C:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe

set NSSM_PATH=%~dp0nssm.exe

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: This script must be run as Administrator
    echo Please run Command Prompt as Administrator and try again
    pause
    exit /b 1
)

REM Check if NSSM exists
if not exist "!NSSM_PATH!" (
    echo Error: nssm.exe not found in !NSSM_PATH!
    echo Please ensure nssm.exe is in the same directory as this script
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "!EXE_PATH!" (
    echo Error: Executable not found at !EXE_PATH!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   Installing AI Test Data Generator as Windows Service
echo ============================================================================
echo.
echo Service Name:  !SERVICE_NAME!
echo Executable:    !EXE_PATH!
echo.

REM Check if service already exists
"!NSSM_PATH!" status "!SERVICE_NAME!" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo Service already exists. Stopping and removing...
    "!NSSM_PATH!" stop "!SERVICE_NAME!" >nul 2>&1
    "!NSSM_PATH!" remove "!SERVICE_NAME!" confirm >nul 2>&1
    echo Service removed.
    echo.
)

REM Create the service
echo Installing service...
"!NSSM_PATH!" install "!SERVICE_NAME!" "!EXE_PATH!"
if !ERRORLEVEL! neq 0 (
    echo Error: Failed to install service
    pause
    exit /b 1
)

REM Configure service to auto-start
echo Configuring auto-start...
"!NSSM_PATH!" set "!SERVICE_NAME!" Start SERVICE_AUTO_START

REM Configure restart on crash (5-second delay)
echo Configuring auto-restart on failure...
"!NSSM_PATH!" set "!SERVICE_NAME!" AppRestartDelay 5000

REM Configure logging to capture stdout/stderr
set LOG_DIR=C:\ProgramData\AITestDataGenerator\logs
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"

echo Configuring logging to !LOG_DIR!...
"!NSSM_PATH!" set "!SERVICE_NAME!" AppStdout "!LOG_DIR!\service.log"
"!NSSM_PATH!" set "!SERVICE_NAME!" AppStderr "!LOG_DIR!\service.log"
"!NSSM_PATH!" set "!SERVICE_NAME!" AppStdoutCreationDisposition 4
"!NSSM_PATH!" set "!SERVICE_NAME!" AppStderrCreationDisposition 4

REM Set service to run as NETWORK SERVICE (local account with minimal privileges)
echo Setting service account to NETWORK SERVICE...
sc config "!SERVICE_NAME!" obj= "NT AUTHORITY\NETWORK SERVICE"

REM Verify installation
echo.
echo Verifying installation...
"!NSSM_PATH!" status "!SERVICE_NAME!"
if !ERRORLEVEL! neq 0 (
    echo Error: Service was created but verification failed
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   ✅ Service installed successfully!
echo ============================================================================
echo.
echo Service Name: !SERVICE_NAME!
echo Status:       Installed (not yet started)
echo.
echo To manage the service, use:
echo   • Start:     net start !SERVICE_NAME!
echo   • Stop:      net stop !SERVICE_NAME!
echo   • Restart:   net stop !SERVICE_NAME! ^&^& net start !SERVICE_NAME!
echo   • Status:    sc query !SERVICE_NAME!
echo   • Remove:    "!NSSM_PATH!" remove !SERVICE_NAME! confirm
echo.
echo Logs: !LOG_DIR!\service.log
echo.
echo API will be accessible at: http://localhost:9090/docs
echo.
pause
