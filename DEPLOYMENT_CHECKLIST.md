# AI Test Data Generator - Deployment Checklist

## Pre-Deployment (Preparation Phase)

### Hardware & Network Verification
- [ ] Server meets minimum requirements (8GB RAM, AVX CPU, Windows Server 2016+)
- [ ] Port 9090 is available and not blocked by firewall
- [ ] Administrator access available on target server
- [ ] Network connectivity verified (if remote deployment)

### Package Preparation
- [ ] All package files downloaded and verified
- [ ] NSSM executable downloaded (`nssm.exe` from https://nssm.cc/download)
- [ ] Package files copied to `C:\Program Files\AITestDataGenerator\`
- [ ] File integrity verified (215.72 MB executable)

### Documentation Review
- [ ] Read DEPLOYMENT.md (Installation guide)
- [ ] Read INTEGRATION.md (How to call from applications)
- [ ] Review system requirements and CPU compatibility
- [ ] Understand service management commands

---

## Deployment (Installation Phase)

### Step 1: Copy Files to Server
```cmd
Destination: C:\Program Files\AITestDataGenerator\

Files:
  ✓ AI-TestData-Generator.exe (215.72 MB)
  ✓ nssm.exe
  ✓ deploy.bat
  ✓ manage_service.bat
  ✓ cache_model.py (optional)
```

- [ ] Executable copied
- [ ] NSSM executable present
- [ ] Scripts copied
- [ ] Directory permissions verified

### Step 2: Run Deployment Script
```cmd
cd C:\Program Files\AITestDataGenerator
deploy.bat
```

**Script Actions:**
- [ ] Creates Windows Service: `AITestDataGenerator`
- [ ] Configures auto-start on system boot
- [ ] Sets up logging directory: `C:\ProgramData\AITestDataGenerator\logs\`
- [ ] Configures crash recovery (5-second restart)
- [ ] Sets service account to NETWORK SERVICE

**Verification:**
- [ ] Script completes without errors
- [ ] Service appears in Windows Services (`services.msc`)
- [ ] Service status shows "Installed"

---

## Post-Deployment (Verification Phase)

### Service Startup
```cmd
manage_service.bat start
```

- [ ] Command executes successfully
- [ ] No error messages
- [ ] Service status changes to "RUNNING"

### API Endpoint Verification
```
http://localhost:9090/docs
```

- [ ] Swagger UI page loads (status 200)
- [ ] API endpoints listed:
  - [ ] POST /api/v1/generate/from-json
  - [ ] POST /api/v1/generate/from-excel
  - [ ] GET /api/v1/health

### Health Check
```powershell
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/health" -UseBasicParsing
```

- [ ] Response code: 200 OK
- [ ] Health status indicates "healthy"
- [ ] Service availability confirmed

### Log Verification
```
C:\ProgramData\AITestDataGenerator\logs\service.log
```

- [ ] Log file created and contains entries
- [ ] Startup messages logged:
  - [ ] "Starting AI Test Data Generator"
  - [ ] "Warming up embedding model"
  - [ ] "FAISS ready: 155 vectors indexed"
  - [ ] "Uvicorn running on http://127.0.0.1:9090"

---

## Integration Testing (Functional Verification)

### Test 1: Basic JSON Generation
```powershell
$input = @{ fields = @(@{ name = "test_field"; sample_value = "test" }); num_records = 1 } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/generate/from-json" -Method POST -Body $input -UseBasicParsing
```

- [ ] Request accepted (status 200/422 with validation error is OK)
- [ ] Response contains generated data or validation feedback
- [ ] No 500 errors

### Test 2: Service Restart
```cmd
manage_service.bat restart
```

- [ ] Service stops cleanly
- [ ] Service restarts automatically
- [ ] API accessible after restart: http://localhost:9090/docs (status 200)
- [ ] Logs show shutdown and restart

### Test 3: Crash Recovery
```powershell
Stop-Process -Name "AI-TestData-Generator.exe" -Force
Start-Sleep -Seconds 10
Invoke-WebRequest -Uri "http://localhost:9090/docs" -UseBasicParsing
```

- [ ] Service auto-restarts within 5 seconds
- [ ] API responsive after auto-restart
- [ ] Logs show crash and recovery

### Test 4: Network Access (if needed)
```
http://[server-ip]:9090/docs
http://[server-hostname]:9090/docs
```

- [ ] Firewall rule added (if network access required)
- [ ] Remote clients can reach the service
- [ ] Status code 200 from remote

---

## Configuration & Customization (Optional)

### Change Port (if 9090 not suitable)
- [ ] Identify new port number
- [ ] Update environment variable or rebuild executable
- [ ] Restart service
- [ ] Verify API at new port

### Change Log Directory
- [ ] Create new directory with proper permissions
- [ ] Update NSSM configuration:
  ```cmd
  nssm set AITestDataGenerator AppStdout "C:\CustomLogs\service.log"
  ```
- [ ] Restart service
- [ ] Verify logs in new location

### Configure Network Binding
- [ ] If remote clients needed: change bind address from 127.0.0.1 to 0.0.0.0
- [ ] Add firewall exception for port 9090
- [ ] Restart service
- [ ] Test from remote machine

---

## Enterprise Application Integration

### .NET / C# Integration
- [ ] Code reviewed (see INTEGRATION.md)
- [ ] HttpClient configured
- [ ] Retry logic implemented (recommended)
- [ ] Error handling in place
- [ ] Tested with sample data

### Python Integration
- [ ] Code reviewed (see INTEGRATION.md)
- [ ] requests library installed
- [ ] Session management configured
- [ ] Error handling implemented
- [ ] Tested with sample data

### JavaScript Integration
- [ ] Code reviewed (see INTEGRATION.md)
- [ ] axios or fetch configured
- [ ] Error handling in place
- [ ] Tested with sample data

### Other Languages
- [ ] Appropriate client code implemented
- [ ] Simple HTTP POST call verified
- [ ] Sample integration tested

---

## Performance & Monitoring Setup

### Baseline Performance Metrics
```powershell
# CPU Usage
(Get-Process AI-TestData-Generator).CPU

# Memory Usage
[Math]::Round((Get-Process AI-TestData-Generator).WorkingSet / 1MB) # MB
```

- [ ] CPU usage at idle: < 5%
- [ ] Memory usage: 2-4 GB (normal for ML libraries)
- [ ] Metrics documented for comparison

### Monitoring Configuration
- [ ] Log directory monitored for growth
- [ ] Service status monitored (optional: external monitoring tool)
- [ ] Error alerts configured (optional)
- [ ] Health check scheduled (optional: automated monitoring)

### Scheduled Maintenance (Recommended for Production)
- [ ] Weekly restart scheduled (maintenance window)
- [ ] Log rotation configured or monitored
- [ ] Disk space for logs verified

---

## Operational Procedures

### Regular Operations
- [ ] Daily: Monitor logs for errors
- [ ] Weekly: Verify service status and health
- [ ] Monthly: Review performance metrics and logs

### Emergency Procedures
- [ ] Service stops responding:
  ```cmd
  manage_service.bat restart
  ```
- [ ] Logs full/corrupted:
  ```cmd
  cd C:\ProgramData\AITestDataGenerator\logs
  del *.log
  manage_service.bat restart
  ```
- [ ] Need to uninstall:
  ```cmd
  manage_service.bat remove
  ```

---

## Decommissioning / Uninstallation

When ready to remove the service:

### Step 1: Stop Service
```cmd
manage_service.bat stop
```
- [ ] Service stopped cleanly

### Step 2: Remove Service
```cmd
manage_service.bat remove
```
- [ ] Service removed from Windows
- [ ] Service no longer appears in services.msc

### Step 3: Clean Up Files
```powershell
Remove-Item -Path "C:\Program Files\AITestDataGenerator" -Recurse -Force
Remove-Item -Path "C:\ProgramData\AITestDataGenerator" -Recurse -Force
```
- [ ] Application directory deleted
- [ ] Logs directory deleted
- [ ] Disk space reclaimed (215+ MB)

---

## Sign-Off & Documentation

### Deployment Completion
- [ ] Date deployed: _______________
- [ ] Deployed by: _______________
- [ ] Verified by: _______________
- [ ] Environment: ☐ Development ☐ Staging ☐ Production

### Change Log Entry
```
Date: [Today's Date]
Action: Deployed AI Test Data Generator as Windows Service
Service: AITestDataGenerator
Port: 9090
Status: RUNNING
Verified: ✓ All tests passed
```

### Contact Information
- **Support Email**: [Your Support Email]
- **Documentation**: DEPLOYMENT.md, INTEGRATION.md
- **Logs Location**: C:\ProgramData\AITestDataGenerator\logs\service.log
- **Management**: manage_service.bat or services.msc

---

## Troubleshooting Quick Reference

| Issue | Solution | Checklist |
|-------|----------|-----------|
| Service won't start | Check CPU AVX support, review logs | [ ] CPU compatible [ ] Logs checked [ ] Restarted |
| API not responding | Check firewall, verify service running | [ ] Firewall checked [ ] Service running [ ] Port available |
| High memory | Normal for ML libs, monitor with updates | [ ] Monitoring enabled [ ] Documented [ ] Alert threshold set |
| Crashes frequently | Check available disk, memory, CPU resources | [ ] Disk space checked [ ] RAM available [ ] CPU monitored |
| Startup slow | First-time model loading, cache rebuilding | [ ] Model cached [ ] FAISS loaded [ ] Normal after first run |

**For detailed troubleshooting, see DEPLOYMENT.md → Troubleshooting section**

---

## Final Verification

Before declaring deployment complete:

```
☐ Service installed and running
☐ API responding on port 9090
☐ Health check returns healthy status
☐ Logs created and monitoring
☐ Enterprise application successfully calling service
☐ Restart recovery working
☐ Documentation reviewed by operations team
☐ Support contacts identified
☐ Monitoring/alerting configured (if applicable)
☐ Deployment documented and signed off
```

---

**🎉 Congratulations! Your deployment is complete.**

Your AI Test Data Generator is now running as a Windows Service and ready for enterprise integration!

**Next:** Review INTEGRATION.md for code examples to embed the service into your applications.
