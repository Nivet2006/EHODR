Write-Host "[INFO] Stopping all running Python/Streamlit processes..." -ForegroundColor Red
taskkill.exe /F /IM python* /T 2>$null
taskkill.exe /F /IM streamlit* /T 2>$null

Write-Host "[INFO] Shutting down Docker containers..." -ForegroundColor Red
docker compose down 2>$null

Write-Host "[SUCCESS] All processes stopped." -ForegroundColor Green
