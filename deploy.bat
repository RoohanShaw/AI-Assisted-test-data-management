@echo off
REM Deploy AI Test Data Generator as Windows Service
REM This script sets up the service with automatic start and crash recovery

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo   AI Test Data Generator - Windows Service Deployment Setup
echo ============================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Please:
    echo   1. Press Win+R
    echo   2. Type "cmd"
    echo   3. Right-click and select "Run as Administrator"
    echo   4. Navigate to this directory
    echo   5. Run: deploy.bat
    echo.
    pause
    exit /b 1
)

REM Check if nssm.exe exists
if not exist "%~dp0nssm.exe" (
    echo.
    echo Step 1: Download NSSM (Non-Sucking Service Manager)
    echo ========================================================
    echo.
    echo NSSM is required to install the service. Please download it manually:
    echo.
    echo 1. Visit: https://nssm.cc/download
    echo 2. Download the latest version (e.g., nssm-2.24-101-g897c7f7.zip)
    echo 3. Extract the ZIP file
    echo 4. Copy nssm.exe from the win64 folder to this directory:
    echo    %~dp0
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

REM Configuration
set SERVICE_NAME=AITestDataGenerator
set EXE_PATH="%~dp0dist\AI-TestData-Generator.exe"
set NSSM_PATH="%~dp0nssm.exe"
set LOG_DIR=C:\ProgramData\AITestDataGenerator\logs

echo Step 1: Verify Executable
echo ========================================================
if not exist %EXE_PATH% (
    echo.
    echo ERROR: Executable not found!
    echo Expected: %EXE_PATH%
    echo.
    echo Please ensure:
    echo   1. The .exe was built successfully (run: pyinstaller AI-TestData-Generator.spec)
    echo   2. The executable is in the dist\ folder
    echo.
    pause
    exit /b 1
)
echo ✓ Executable found: %EXE_PATH%
echo.

echo Step 2: Create Log Directory
echo ========================================================
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    echo ✓ Log directory created: %LOG_DIR%
) else (
    echo ✓ Log directory already exists: %LOG_DIR%
)
echo.

echo Step 3: Install Windows Service
echo ========================================================
echo Service Name: %SERVICE_NAME%
echo Executable:   %EXE_PATH%
echo Logs:         %LOG_DIR%
echo.

REM Check if service already exists and remove it
%NSSM_PATH% status "%SERVICE_NAME%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Removing existing service...
    net stop "%SERVICE_NAME%" >nul 2>&1
    %NSSM_PATH% remove "%SERVICE_NAME%" confirm >nul 2>&1
    timeout /t 2 >nul
)

REM Install the service
echo Installing service...
%NSSM_PATH% install "%SERVICE_NAME%" %EXE_PATH%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

REM Configure service startup
echo Configuring auto-start on system boot...
%NSSM_PATH% set "%SERVICE_NAME%" Start SERVICE_AUTO_START

REM Configure restart on crash (5-second delay)
echo Configuring crash recovery...
%NSSM_PATH% set "%SERVICE_NAME%" AppRestartDelay 5000

REM Configure logging
echo Configuring logging...
%NSSM_PATH% set "%SERVICE_NAME%" AppStdout "%LOG_DIR%\service.log"
%NSSM_PATH% set "%SERVICE_NAME%" AppStderr "%LOG_DIR%\service.log"
%NSSM_PATH% set "%SERVICE_NAME%" AppStdoutCreationDisposition 4
%NSSM_PATH% set "%SERVICE_NAME%" AppStderrCreationDisposition 4

REM Set service account
echo Configuring service account (NETWORK SERVICE)...
sc config "%SERVICE_NAME%" obj= "NT AUTHORITY\NETWORK SERVICE" >nul 2>&1

echo.
echo Step 4: Verify Installation
echo ========================================================
%NSSM_PATH% status "%SERVICE_NAME%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Service installation failed
    pause
    exit /b 1
)
echo ✓ Service installed successfully
echo.

echo.
echo ============================================================================
echo   ✅ Deployment Complete!
echo ============================================================================
echo.
echo Service Name:  %SERVICE_NAME%
echo Status:        Installed (not yet started)
echo Port:          9090
echo.
echo Next Steps:
echo.
echo 1. START the service:
echo    manage_service.bat start
echo.
echo 2. ACCESS the API:
echo    http://localhost:9090/docs
echo.
echo 3. SERVICE MANAGEMENT:
echo    manage_service.bat start      - Start the service
echo    manage_service.bat stop       - Stop the service
echo    manage_service.bat restart    - Restart the service
echo    manage_service.bat status     - Check service status
echo.
echo 4. VIEW LOGS:
echo    %LOG_DIR%\service.log
echo.
echo Resources:
echo    • API Documentation:    http://localhost:9090/docs
echo    • Health Check:         http://localhost:9090/api/v1/health
echo    • Generate Data (JSON): POST http://localhost:9090/api/v1/generate/from-json
echo    • Generate Data (Excel): POST http://localhost:9090/api/v1/generate/from-excel
echo.
echo ============================================================================
echo.
pause
