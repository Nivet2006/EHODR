$on8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($on8080) {
  Write-Host "[WARN] Port 8080 is in use. Stop the old server (Ctrl+C) or: Stop-Process -Id $($on8080[0].OwningProcess) -Force" -ForegroundColor Yellow
}
Write-Host "[INFO] Starting EHODR Command Dashboards (live API)..." -ForegroundColor Green
Write-Host "       Hub:       http://localhost:8080" -ForegroundColor Cyan
Write-Host "       Ambulance: http://localhost:8080/ambulance.html" -ForegroundColor Cyan
Write-Host "       Guardian:  http://localhost:8080/guardian.html" -ForegroundColor Cyan
Write-Host "       ER Command: http://localhost:8080/er-command.html" -ForegroundColor Cyan
Write-Host "       Press Ctrl+C to stop." -ForegroundColor DarkGray
Set-Location $PSScriptRoot
python dashboards\serve.py
