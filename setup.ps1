# Game Design Planner - Bootstrapper Installer & Launcher
# This script ensures Python, Ollama, required libraries, and the Gemma model are installed.

$ErrorActionPreference = "Stop"

# Define local paths
$LocalPythonDir = Join-Path $PSScriptRoot ".python"
$PythonExe = Join-Path $LocalPythonDir "python.exe"
$RequirementsFile = Join-Path $PSScriptRoot "requirements.txt"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "     Gemma 4 UEFN Game Planner Setup Launcher     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Register Custom Protocol Handler (ollama-planner://)
Write-Host "[1/6] Registering custom protocol handler (ollama-planner://)..." -ForegroundColor Green
try {
    $RegistryPath = "HKCU:\Software\Classes\ollama-planner"
    if (-not (Test-Path $RegistryPath)) {
        New-Item -Path $RegistryPath -Force | Out-Null
    }
    # Note: Default properties are set via the empty name ""
    New-ItemProperty -Path $RegistryPath -Name "(Default)" -Value "URL:Ollama Game Planner Protocol" -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $RegistryPath -Name "URL Protocol" -Value "" -PropertyType String -Force | Out-Null

    $CommandPath = "$RegistryPath\shell\open\command"
    if (-not (Test-Path $CommandPath)) {
        New-Item -Path $CommandPath -Force | Out-Null
    }
    $BatchPath = Join-Path $PSScriptRoot "launcher.bat"
    # Execute batch file in its own directory
    $EscapedCommand = "cmd.exe /c cd /d `"$PSScriptRoot`" && launcher.bat"
    New-ItemProperty -Path $CommandPath -Name "(Default)" -Value $EscapedCommand -PropertyType String -Force | Out-Null
    Write-Host "Registered protocol handler successfully." -ForegroundColor Green
} catch {
    Write-Warning "Failed to register custom protocol handler: $_"
}

# 2. Check & Install Ollama
Write-Host ""
Write-Host "[2/6] Checking for Ollama..." -ForegroundColor Green
$OllamaPath = Get-Command ollama -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $OllamaPath) {
    # Check common install locations dynamically
    $CommonPaths = @(
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "$env:PROGRAMFILES\Ollama\ollama.exe",
        "$env:SystemDrive\Users\$env:USERNAME\AppData\Local\Programs\Ollama\ollama.exe",
        "C:\Users\Tesla\AppData\Local\Programs\Ollama\ollama.exe",
        "C:\Program Files\Ollama\ollama.exe"
    )
    foreach ($Path in $CommonPaths) {
        if (Test-Path $Path) {
            $OllamaPath = $Path
            break
        }
    }
}

if (-not $OllamaPath) {
    Write-Host "Ollama was not found on your system." -ForegroundColor Yellow
    Write-Host "Downloading Ollama installer..." -ForegroundColor Yellow
    $OllamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $TempOllamaExe = Join-Path $env:TEMP "OllamaSetup.exe"
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $OllamaUrl -OutFile $TempOllamaExe -UseBasicParsing
    
    Write-Host "Running Ollama Installer... Please complete the quick setup dialog." -ForegroundColor Cyan
    Start-Process -FilePath $TempOllamaExe -Wait
    
    # Wait for path update or local detection
    $OllamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (-not (Test-Path $OllamaPath)) {
        Start-Sleep -Seconds 3
        if (-not (Test-Path $OllamaPath)) {
            Write-Warning "Failed to locate Ollama after installation. Please launch Ollama manually and restart this script."
            Read-Host "Press Enter to exit..."
            Exit
        }
    }
    Write-Host "Ollama installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Ollama is already installed at: $OllamaPath" -ForegroundColor Green
}

# 3. Check & Set Up Python
Write-Host ""
Write-Host "[3/6] Checking for Python..." -ForegroundColor Green
$SystemPython = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source

if (Test-Path $PythonExe) {
    Write-Host "Using existing local portable Python environment." -ForegroundColor Green
} elseif ($SystemPython) {
    Write-Host "Using system Python: $SystemPython" -ForegroundColor Green
    $PythonExe = $SystemPython
} else {
    Write-Host "Python not found. Setting up a portable Python environment..." -ForegroundColor Yellow
    
    # Create local directory
    if (-not (Test-Path $LocalPythonDir)) {
        New-Item -ItemType Directory -Path $LocalPythonDir | Out-Null
    }
    
    # Download Embeddable Python (3.11.9)
    $PythonZipUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    $TempZip = Join-Path $env:TEMP "python-portable.zip"
    Write-Host "Downloading portable Python zip..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PythonZipUrl -OutFile $TempZip -UseBasicParsing
    
    Write-Host "Extracting Python environment..." -ForegroundColor Yellow
    Expand-Archive -Path $TempZip -DestinationPath $LocalPythonDir -Force
    
    # Configure path file to enable site-packages (required for pip to work in embeddable python)
    $PthFile = Join-Path $LocalPythonDir "python311._pth"
    if (Test-Path $PthFile) {
        $Content = Get-Content $PthFile
        $UpdatedContent = $Content -replace '#import site', 'import site'
        Set-Content -Path $PthFile -Value $UpdatedContent
    }
    
    # Install Pip
    Write-Host "Downloading pip package manager bootstrapper..." -ForegroundColor Yellow
    $GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
    $GetPipFile = Join-Path $LocalPythonDir "get-pip.py"
    Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipFile -UseBasicParsing
    
    Write-Host "Installing pip..." -ForegroundColor Yellow
    Start-Process -FilePath $PythonExe -ArgumentList "$GetPipFile" -NoNewWindow -Wait
    
    Write-Host "Portable Python configuration completed successfully!" -ForegroundColor Green
}

# 4. Install Requirements
Write-Host ""
Write-Host "[4/6] Installing required packages..." -ForegroundColor Green
if (Test-Path $RequirementsFile) {
    Start-Process -FilePath $PythonExe -ArgumentList "-m pip install -r `"$RequirementsFile`"" -NoNewWindow -Wait
    Write-Host "Packages checked/installed successfully." -ForegroundColor Green
} else {
    Write-Warning "requirements.txt was not found! Skipping library installations."
}

# 5. Pull Gemma Model
Write-Host ""
Write-Host "[5/6] Pre-fetching Gemma model weights..." -ForegroundColor Green
Write-Host "Running 'ollama pull gemma4:latest' in the background..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "pull gemma4:latest" -NoNewWindow -Wait
Write-Host "Model verification completed." -ForegroundColor Green

# 6. Start Application Server
Write-Host ""
Write-Host "[6/6] Launching FastAPI local server..." -ForegroundColor Green
Write-Host "Opening Game Design Planner in your default browser..." -ForegroundColor Cyan

# Launch server in background
Start-Process -FilePath $PythonExe -ArgumentList "server.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden

# Wait for server startup
Start-Sleep -Seconds 3

# Launch GitHub Pages frontend link
Start-Process "https://RorriMaesu.github.io/gemma4-uefn-game-planner/"

Write-Host "All systems operational! You can close this script window." -ForegroundColor Green
Start-Sleep -Seconds 5
