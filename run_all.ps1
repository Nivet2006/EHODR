Write-Host "[INFO] Starting Universal AI Memory System (Docker Containers)..." -ForegroundColor Cyan
docker compose up -d

Write-Host "[WAIT] Waiting 5 seconds for services to boot..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[INFO] Initializing databases and vector collections..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe scripts/init_qdrant_collections.py

Write-Host "[INFO] Starting Hospital Resource Optimizer Dashboard (Streamlit)..." -ForegroundColor Green
& .\venv\Scripts\streamlit.exe run app_enhanced.py
