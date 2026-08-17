# AI Test Data Generator - Windows Service Deployment Package

## Package Contents

This deployment package contains everything needed to deploy the AI Test Data Generator as a Windows Service.

### Files Included

```
├── AI-TestData-Generator.exe              (215.72 MB)
│   └── Self-contained executable with all dependencies bundled
│       ├── FastAPI server
│       ├── PyTorch + FAISS (AI/ML libraries)
│       ├── SentenceTransformer model (all-MiniLM-L6-v2)
│       ├── Pre-computed FAISS index (155 vectors)
│       └── Faker + other dependencies
│
├── DEPLOYMENT.md                           (Comprehensive deployment guide)
│   └── System requirements, installation steps, configuration, troubleshooting
│
├── INTEGRATION.md                          (Enterprise integration guide)
│   └── Code examples in C#, Python, JavaScript, Java, PowerShell
│   └── API reference, error handling, performance tuning
│
├── deploy.bat                              (Automated deployment script)
│   └── Downloads/installs NSSM, creates Windows Service
│
├── manage_service.bat                      (Service management script)
│   └── Start, stop, restart, status, remove service
│
├── cache_model.py                          (Pre-cache model)
│   └── Downloads embedding model (optional, already included)
│
├── nssm.exe                                (Service manager)
│   └── Non-Sucking Service Manager (MUST be downloaded separately)
│
└── README.md                               (This file)
```

## Quick Start (5 Minutes)

### Step 1: Download NSSM

1. Visit: https://nssm.cc/download
2. Download latest version (e.g., `nssm-2.24-101-g897c7f7.zip`)
3. Extract and copy `nssm.exe` from `win64` folder to this directory

### Step 2: Deploy Service

1. Open **Command Prompt as Administrator**
2. Navigate to this directory:
   ```cmd
   cd "C:\Path\To\Deployment\Package"
   ```
3. Run deployment:
   ```cmd
   deploy.bat
   ```
4. Follow on-screen instructions

### Step 3: Start Service

```cmd
manage_service.bat start
```

### Step 4: Access API

Open browser: **http://localhost:9090/docs**

## Deployment Overview

```
┌─────────────────────────────────────────────────────────┐
│          Your Enterprise Server (Windows)               │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1: Copy Executable & Scripts                       │
│  • AI-TestData-Generator.exe → C:\Program Files\...     │
│  • *.bat scripts → Same directory                       │
│  • nssm.exe → Same directory                            │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: Run deploy.bat (Admin)                          │
│  • Creates Windows Service                              │
│  • Configures auto-start                                │
│  • Sets up logging                                      │
│  • Enables crash recovery                               │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: Start Service                                   │
│  • manage_service.bat start                             │
│  • Service auto-starts on server reboot                 │
│  • Auto-restarts if it crashes                          │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4: Enterprise Apps Call Service                    │
│  • http://localhost:9090/api/v1/generate                │
│  • See INTEGRATION.md for code examples                 │
└─────────────────────────────────────────────────────────┘
```

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows Server 2016+ or Windows 10/11 Pro |
| **CPU** | Modern Intel/AMD with AVX instruction set |
| **RAM** | 8 GB minimum, 16 GB recommended |
| **Disk** | 500 MB + 2 GB operating space |
| **Port** | 9090 (configurable) |

## What Gets Installed

When you run `deploy.bat`, it:

1. ✅ Verifies Windows Service Manager is available
2. ✅ Creates `AITestDataGenerator` Windows Service
3. ✅ Configures auto-start on system boot
4. ✅ Configures auto-restart on crash (5-second delay)
5. ✅ Sets up logging to `C:\ProgramData\AITestDataGenerator\logs\service.log`
6. ✅ Configures to run as `NETWORK SERVICE` (minimal privileges)
7. ✅ Makes API available at `http://localhost:9090`

## File Specifications

| File | Size | Purpose |
|------|------|---------|
| AI-TestData-Generator.exe | 215.72 MB | Main executable (all deps bundled) |
| DEPLOYMENT.md | ~15 KB | Installation & configuration guide |
| INTEGRATION.md | ~30 KB | Code examples for enterprise apps |
| deploy.bat | ~5 KB | Automated setup script |
| manage_service.bat | ~3 KB | Service management script |

**Total Package Size**: ~215 MB (mostly the executable)

## API Features

The deployed service provides:

- **Generate Test Data**: POST /api/v1/generate/from-json
- **Upload Excel**: POST /api/v1/generate/from-excel
- **Health Check**: GET /api/v1/health
- **API Docs**: GET /docs (Swagger UI)
- **API Docs (ReDoc)**: GET /redoc

## Configuration

### Change Port from 9090

Edit `start.py` before building the executable, or use environment variables:

```powershell
[Environment]::SetEnvironmentVariable("APP_PORT", "9091", "User")
```

### Change Log Directory

```cmd
nssm set AITestDataGenerator AppStdout "C:\MyLogs\service.log"
```

### Configure for Network Access

Modify binding from `127.0.0.1` to `0.0.0.0` in `start.py` before building.

## Troubleshooting

### Service Won't Start
- Check CPU has AVX support (run CPU compatibility test)
- Review logs: `C:\ProgramData\AITestDataGenerator\logs\service.log`
- Verify executable exists: `C:\Program Files\AITestDataGenerator\AI-TestData-Generator.exe`

### API Not Responding
- Verify service is running: `manage_service.bat status`
- Check port 9090 is not blocked by firewall
- Test directly: `curl http://localhost:9090/docs`

### High Memory Usage
- Normal: AI/ML libraries (PyTorch, FAISS) require 2-4 GB RAM
- Monitor: `tasklist /v | findstr AI-TestData`

See **DEPLOYMENT.md** for comprehensive troubleshooting.

## Service Management

```cmd
# Start
manage_service.bat start
net start AITestDataGenerator

# Stop
manage_service.bat stop
net stop AITestDataGenerator

# Restart
manage_service.bat restart

# Status
manage_service.bat status
sc query AITestDataGenerator

# Remove
manage_service.bat remove
```

## Integration Examples

### C# / .NET
```csharp
var response = await client.PostAsync(
    "http://localhost:9090/api/v1/generate/from-json",
    new StringContent(jsonInput, Encoding.UTF8, "application/json"));
```

### Python
```python
response = requests.post(
    "http://localhost:9090/api/v1/generate/from-json",
    json=input_data)
```

### JavaScript
```javascript
const response = await fetch(
    "http://localhost:9090/api/v1/generate/from-json",
    { method: "POST", body: JSON.stringify(inputData) });
```

See **INTEGRATION.md** for complete examples in 6 languages.

## Performance

| Metric | Value |
|--------|-------|
| Startup Time | ~5-10 seconds |
| Concurrent Requests | ~10 (default) |
| Data Generation Rate | ~100 records/second |
| Memory Usage | 2-4 GB (model + FAISS) |
| CPU Usage | Low during idle, moderate during generation |

## Monitoring

### Health Check
```powershell
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/health" -UseBasicParsing
```

### View Logs
```powershell
Get-Content -Path "C:\ProgramData\AITestDataGenerator\logs\service.log" -Wait
```

### Service Status
```powershell
Get-Service AITestDataGenerator
tasklist | findstr AI-TestData
```

## Next Steps

1. **Install**: Run `deploy.bat` (Admin)
2. **Start**: Run `manage_service.bat start`
3. **Test**: Open http://localhost:9090/docs
4. **Integrate**: Follow examples in INTEGRATION.md
5. **Monitor**: Check logs regularly

## Support & Documentation

- **Interactive API Docs**: http://localhost:9090/docs (Swagger UI)
- **Installation Guide**: See DEPLOYMENT.md
- **Integration Guide**: See INTEGRATION.md
- **Code Examples**: See INTEGRATION.md (C#, Python, JS, Java, PowerShell)
- **Logs**: C:\ProgramData\AITestDataGenerator\logs\service.log

## Security Notes

⚠️ **Important for Production**:

- Service runs as `NETWORK SERVICE` (minimal privileges)
- Exposed to localhost by default (127.0.0.1)
- For network access: Use firewall rules, consider HTTPS reverse proxy
- No authentication by default (add if exposed to untrusted networks)
- Logs are not encrypted (use OS-level encryption if needed)

## Version Information

- **Version**: 1.0.0
- **Build Date**: August 1, 2026
- **Python**: 3.10
- **FastAPI**: 0.115
- **PyTorch**: 2.5.1 (CPU)
- **FAISS**: 1.9.0 (CPU)

## License & Attribution

[Include appropriate licenses for included components]

---

**Ready to deploy?** Start with Step 1 in "Quick Start" section above! 🚀
