# Executable Build Guide

This document explains how to create a fresh Windows executable for the AI Test Data Generator whenever a new code push is made.

## 1. What is used to build the EXE

The project already includes a PyInstaller spec file:

- `AI-TestData-Generator.spec`

This spec builds the main executable from `start.py` and outputs the file to:

- `dist\AI-TestData-Generator.exe`

The project also includes:

- `deploy.bat` — builds the executable if missing and installs the service
- `launcher.spec` — a second spec for the launcher UI

---

## 2. Manual local build

From the project root:

```powershell
cd "C:\Work-Transitus\SNAPAITestGenerator_Version2\AI-Assisted-test-data-management"

py -3 -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements_actual.txt
pip install pyinstaller

py -3 -m PyInstaller "AI-TestData-Generator.spec" --clean
```

Expected output:

- `dist\AI-TestData-Generator.exe`

This script verifies the executable exists, builds it automatically if missing, and then continues with Windows service installation.

---
# Future


## 3. Build steps after every code push

Recommended flow:

1. Pull or push the latest code
2. Install dependencies
3. Run the build command
4. Generate the EXE artifact
5. Archive or publish the file for deployment

### Example Windows PowerShell build script

Save this as `build_exe.ps1` in the project root:

```powershell
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv")) {
    py -3 -m venv venv
}

. .\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements_actual.txt
pip install pyinstaller

py -3 -m PyInstaller "AI-TestData-Generator.spec" --clean

if (-not (Test-Path ".\dist\AI-TestData-Generator.exe")) {
    throw "Build failed: dist\AI-TestData-Generator.exe was not created."
}

Write-Host "Executable created successfully: .\dist\AI-TestData-Generator.exe"
```

Run it with:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

---

## 4. Automatic generation on Git push

To generate the EXE automatically whenever code is pushed, use a CI workflow. Below is a sample GitHub Actions workflow.

Create a file named `.github/workflows/build-exe.yml`:

```yaml
name: Build Windows EXE

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-exe:
    runs-on: windows-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements_actual.txt
          pip install pyinstaller

      - name: Build EXE
        run: |
          py -3 -m PyInstaller "AI-TestData-Generator.spec" --clean

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: AI-TestData-Generator-EXE
          path: .\dist\AI-TestData-Generator.exe
```

This ensures that every push to `main` creates a new build artifact automatically.

---

## 5. Recommended release process

For production deployment, use this sequence:

1. Push code to the branch
2. CI runs the EXE build
3. Download the generated artifact from GitHub Actions
4. Copy the EXE to the deployment folder
5. Install or replace the Windows service using `deploy.bat` or NSSM

---

## 6. Notes

- The repository is already set up for Windows packaging via PyInstaller.
- The main spec file is `AI-TestData-Generator.spec`.
- The build artifact is expected in `dist\AI-TestData-Generator.exe`.
- For repeatable builds, prefer the CI workflow or the `build_exe.ps1` script over manual commands.

---

## 7. Quick command summary

```powershell
py -3 -m PyInstaller "AI-TestData-Generator.spec" --clean
```

This is the core command used to generate a fresh executable after every software update.
