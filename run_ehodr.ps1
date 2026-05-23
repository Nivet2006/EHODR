# EHODR - single launcher: Streamlit optimizer + live command dashboards
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'
$Root = $PSScriptRoot
Set-Location $Root

$PortHub = 8080
$PortOptimizer = 8501

function Stop-EhodrPorts {
    foreach ($port in @($PortHub, $PortOptimizer)) {
        $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Start-Sleep -Milliseconds 500
}

function Wait-Url([string]$Url, [int]$Seconds = 45) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

Write-Host ""
Write-Host "  EHODR - Emergency Hospital Resource Optimizer" -ForegroundColor Cyan
Write-Host "  Starting all dashboards..." -ForegroundColor Cyan
Write-Host ""

$python = "python"
if (Test-Path "$Root\venv\Scripts\python.exe") {
    $python = "$Root\venv\Scripts\python.exe"
}

$streamlit = "$Root\venv\Scripts\streamlit.exe"
if (-not (Test-Path $streamlit)) {
    $streamlit = "streamlit"
}

Stop-EhodrPorts

$serveProc = Start-Process -FilePath $python -ArgumentList "dashboards\serve.py" -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$stProc = Start-Process -FilePath $streamlit -ArgumentList "run","app_enhanced.py","--server.headless","true","--server.port",$PortOptimizer -WorkingDirectory $Root -WindowStyle Hidden -PassThru

Write-Host "[WAIT] Command hub API (port $PortHub)..." -ForegroundColor Yellow
if (-not (Wait-Url "http://127.0.0.1:$PortHub/api/state")) {
    Write-Host "[ERROR] Hub server did not start. Check python dashboards\serve.py" -ForegroundColor Red
    Stop-Process -Id $serveProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $stProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "[WAIT] Optimizer / GIS map (port $PortOptimizer)..." -ForegroundColor Yellow
if (-not (Wait-Url "http://127.0.0.1:$PortOptimizer")) {
    Write-Host "[WARN] Streamlit slow to start - opening hub anyway." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  READY" -ForegroundColor Green
Write-Host "  -------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  Main hub (start here):  http://127.0.0.1:$PortHub/" -ForegroundColor White
Write-Host "  Patient picker + GIS:   http://127.0.0.1:$PortOptimizer/" -ForegroundColor White
Write-Host "  Ambulance:              http://127.0.0.1:$PortHub/ambulance.html" -ForegroundColor DarkGray
Write-Host "  Guardian:               http://127.0.0.1:$PortHub/guardian.html" -ForegroundColor DarkGray
Write-Host "  ER Command:             http://127.0.0.1:$PortHub/er-command.html" -ForegroundColor DarkGray
Write-Host "  -------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop all servers." -ForegroundColor DarkGray
Write-Host ""

Start-Process "http://127.0.0.1:$PortHub/"
Start-Sleep -Milliseconds 800
Start-Process "http://127.0.0.1:$PortOptimizer/"

try {
    while (-not $serveProc.HasExited) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`n[INFO] Stopping EHODR servers..." -ForegroundColor Yellow
    Stop-Process -Id $serveProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $stProc.Id -Force -ErrorAction SilentlyContinue
    Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Stop-EhodrPorts
    Write-Host "[INFO] Stopped." -ForegroundColor Green
}
