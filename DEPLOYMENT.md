# AI Test Data Generator - Windows Service Deployment Guide

## Overview

The **AI Test Data Generator** is a sophisticated synthetic test data engine that can be deployed as a standalone Windows Service on enterprise servers. This guide covers deployment, configuration, and integration into enterprise applications.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Enterprise Server (Windows)              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Test Data Generator (Windows Service)             │  │
│  │                                                       │  │
│  │  FastAPI Server                                      │  │
│  │  ├─ Embedding Engine (SentenceTransformer)           │  │
│  │  ├─ FAISS Vector Index (155 vectors)                 │  │
│  │  ├─ Semantic Classification Pipeline                 │  │
│  │  └─ Mock Data Generator (Faker)                      │  │
│  │                                                       │  │
│  │  Listening on: http://127.0.0.1:9090                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ▲                                   │
│                          │ HTTP Requests                     │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Enterprise Applications (Same Machine or Network)    │  │
│  │  ├─ .NET/C# Applications                             │  │
│  │  ├─ Python Applications                              │  │
│  │  ├─ JavaScript/Node.js Applications                  │  │
│  │  └─ Any HTTP-capable Language                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## System Requirements

### Minimum Specifications
- **OS**: Windows Server 2016 or later (or Windows 10/11 Pro)
- **CPU**: Intel/AMD processor with AVX instruction set support (modern CPUs, 2013+)
- **RAM**: 8 GB (minimum), 16 GB recommended
- **Disk**: 500 MB for executable + dependencies + 2 GB for operating space
- **Network**: Port 9090 available (configurable)

### Recommended Specifications (Production)
- **OS**: Windows Server 2019 or 2022
- **CPU**: Modern Intel Xeon or AMD EPYC with AVX2 support
- **RAM**: 16+ GB
- **Disk**: SSD for logs and temporary files (faster I/O)
- **Network**: Dedicated network for service, firewall properly configured

### CPU Compatibility Check

Before deployment, run the CPU compatibility check:

```powershell
# PowerShell as Administrator
$cpu = (wmi query get description | find "Model Name" | cut -d "=" -f2 | tr -d ' "')
Write-Host "CPU: $cpu"
Write-Host "Checking for AVX support..."

# If the service fails to start, this indicates AVX is not available
# See troubleshooting section below
```

## Deployment Steps

### Step 1: Download NSSM (Non-Sucking Service Manager)

1. Visit: https://nssm.cc/download
2. Download the latest version (e.g., `nssm-2.24-101-g897c7f7.zip`)
3. Extract the ZIP file
4. Copy `nssm.exe` from the `win64` folder to the deployment directory

### Step 2: Prepare Deployment Directory

```powershell
# Create deployment directory
$deployDir = "C:\Program Files\AITestDataGenerator"
New-Item -ItemType Directory -Path $deployDir -Force

# Copy executable
Copy-Item "C:\Work-Transitus\AI-TestData-Generator\dist\AI-TestData-Generator.exe" -Destination $deployDir
Copy-Item "C:\Work-Transitus\AI-TestData-Generator\nssm.exe" -Destination $deployDir
Copy-Item "C:\Work-Transitus\AI-TestData-Generator\deploy.bat" -Destination $deployDir
Copy-Item "C:\Work-Transitus\AI-TestData-Generator\manage_service.bat" -Destination $deployDir
```

### Step 3: Run Deployment Script

1. Open **Command Prompt as Administrator**
2. Navigate to deployment directory:
   ```cmd
   cd C:\Program Files\AITestDataGenerator
   ```
3. Run deployment script:
   ```cmd
   deploy.bat
   ```
4. Follow the prompts to install the service

### Step 4: Start the Service

```cmd
manage_service.bat start
```

Or using native Windows commands:
```cmd
net start AITestDataGenerator
```

### Step 5: Verify Installation

```cmd
manage_service.bat status
```

Check that:
- Service status shows "RUNNING"
- API endpoint responds: `http://localhost:9090/docs` (200 OK)
- Logs are being written to: `C:\ProgramData\AITestDataGenerator\logs\service.log`

## Service Management

### Start Service
```cmd
manage_service.bat start
net start AITestDataGenerator
```

### Stop Service
```cmd
manage_service.bat stop
net stop AITestDataGenerator
```

### Restart Service
```cmd
manage_service.bat restart
net stop AITestDataGenerator && net start AITestDataGenerator
```

### Check Service Status
```cmd
manage_service.bat status
sc query AITestDataGenerator
```

### Remove Service
```cmd
manage_service.bat remove
nssm remove AITestDataGenerator confirm
```

## Configuration

### Change Port

Edit the executable or environment variable before starting the service:

1. **Via Environment Variable** (recommended):
   ```powershell
   [Environment]::SetEnvironmentVariable("APP_PORT", "9091", "User")
   # Then restart service
   ```

2. **Via Command Line** (when running standalone):
   ```cmd
   c:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe --port 9091
   ```

### Change Log Directory

Modify `NSSM` configuration:
```cmd
nssm set AITestDataGenerator AppStdout "C:\MyLogs\service.log"
nssm set AITestDataGenerator AppStderr "C:\MyLogs\service.log"
```

### Change Service Account

By default, service runs as `NETWORK SERVICE` (minimal privileges). To change:
```cmd
sc config AITestDataGenerator obj= "DOMAIN\Username" password= "Password"
```

## Network Configuration

### For Same-Machine Access

Enterprise applications on the same server call the service directly:
```
http://localhost:9090/api/v1/generate
```

### For Network Access (Different Machines)

1. **Enable Firewall Exception**:
   ```powershell
   New-NetFirewallRule -DisplayName "AI Test Data Generator" `
     -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9090
   ```

2. **Configure Binding** (if not localhost-only):
   - Modify `start.py` to bind to `0.0.0.0` instead of `127.0.0.1`
   - Rebuild executable or use environment variable

3. **Call from Remote Machine**:
   ```
   http://server-ip:9090/api/v1/generate
   http://server-hostname:9090/api/v1/generate
   ```

### Security Considerations

- **Internal Networks Only**: The service should only be exposed to internal enterprise networks
- **Authentication**: Add API key validation if exposed to untrusted networks
- **HTTPS**: Consider reverse proxy (IIS/Nginx) with SSL/TLS for production
- **Firewall Rules**: Restrict access to authorized machines/subnets only

## Troubleshooting

### Service Won't Start

**Symptom**: `Error 1053: Service did not respond to start or control request in timely fashion`

**Solutions**:
1. Check CPU compatibility - service requires AVX instruction set
2. Review logs: `C:\ProgramData\AITestDataGenerator\logs\service.log`
3. Try running executable directly: `C:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe`
4. Increase NSSM startup timeout:
   ```cmd
   nssm set AITestDataGenerator AppThrottle 1500
   ```

### API Endpoint Not Responding

**Symptom**: Cannot reach `http://localhost:9090/docs`

**Solutions**:
1. Verify service is running: `manage_service.bat status`
2. Check firewall: Allow port 9090 for local and/or network traffic
3. Check logs for errors: `C:\ProgramData\AITestDataGenerator\logs\service.log`
4. Test service startup manually:
   ```cmd
   C:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe
   ```

### High Memory Usage

**Symptom**: Service consuming excessive RAM (>4GB)

**Solutions**:
1. This is normal for PyTorch/FAISS (AI/ML libraries)
2. Expected usage: 2-4 GB for model + FAISS index
3. Configure Windows to allow virtual memory/paging if needed
4. Monitor via: `tasklist /v | findstr AI-TestData-Generator`

### Crashes After Reboot

**Symptom**: Service fails to start automatically after server reboot

**Solutions**:
1. Verify service auto-start is enabled:
   ```cmd
   sc query AITestDataGenerator
   ```
2. Check for required binaries (PyInstaller dependencies)
3. Review Application Event Log in Event Viewer for clues
4. Try manual start to see detailed error output

### CPU Compatibility Error

**Symptom**: `Illegal instruction` or service crashes immediately

**Causes**: CPU does not support AVX instruction set (older processors)

**Solutions**:
1. Check CPU: `wmic cpu get name`
2. If no AVX support, rebuild with CPU-specific FAISS build
3. Alternative: Use Docker for compatibility (see Docker deployment guide)
4. Document CPU requirement to IT team

## Logging

### Log Location
```
C:\ProgramData\AITestDataGenerator\logs\service.log
```

### Log Format
```
[TIMESTAMP] | [LEVEL] | [MODULE] | [MESSAGE]
2026-08-01 01:10:34,486 | INFO | __main__ | Starting AI Test Data Generator v1.0.0
```

### View Logs (Real-time)
```powershell
Get-Content -Path "C:\ProgramData\AITestDataGenerator\logs\service.log" -Wait
```

### Log Rotation

NSSM appends to the same log file. To implement rotation:

1. Use Windows built-in log rotation (Windows Server 2016+):
   ```powershell
   # Use Event Log instead
   nssm set AITestDataGenerator AppEventLog Application
   ```

2. Or use external tool (logrotate for Windows)

## Monitoring & Maintenance

### Health Check Endpoint

Test service availability:
```powershell
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/health" -UseBasicParsing
```

Expected response: `200 OK` with health details

### Performance Metrics

Monitor service health:
```powershell
# CPU usage
(Get-Process AI-TestData-Generator -ErrorAction SilentlyContinue).CPU

# Memory usage
(Get-Process AI-TestData-Generator -ErrorAction SilentlyContinue).WorkingSet / 1MB

# Check uptime
Get-ServiceUptime -Name AITestDataGenerator
```

### Scheduled Restarts

For production environments, consider scheduled weekly restarts:
```powershell
# Create scheduled task (PowerShell as Administrator)
$action = New-ScheduledTaskAction -Execute "net" -Argument "stop AITestDataGenerator"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 02:00AM
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Restart-AITestDataGenerator" -Description "Weekly restart of AI Test Data Generator"
```

## Uninstallation

### Remove Service
```cmd
manage_service.bat remove
```

Or manually:
```cmd
nssm remove AITestDataGenerator confirm
net stop AITestDataGenerator
```

### Clean Up
```powershell
Remove-Item -Path "C:\Program Files\AITestDataGenerator" -Recurse -Force
Remove-Item -Path "C:\ProgramData\AITestDataGenerator" -Recurse -Force
```

## Support & Documentation

- **API Documentation**: http://localhost:9090/docs (Swagger UI)
- **ReDoc**: http://localhost:9090/redoc
- **GitHub**: [Repository Link]
- **Issues**: Submit issues with service logs included

## Next Steps

- See [Enterprise Integration Guide](INTEGRATION.md) for calling endpoints from enterprise applications
- See [API Reference](API_REFERENCE.md) for detailed endpoint documentation
- See [Sample Clients](samples/) for code examples in your language
