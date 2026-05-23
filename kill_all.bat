@echo off
echo [INFO] Stopping all running Python/Streamlit processes...
taskkill /F /IM python* /T >nul 2>&1
taskkill /F /IM streamlit* /T >nul 2>&1

echo [INFO] Shutting down Docker containers...
docker compose down >nul 2>&1

echo [SUCCESS] All processes stopped.
