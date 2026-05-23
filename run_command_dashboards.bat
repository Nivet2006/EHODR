@echo off
echo [INFO] Starting EHODR Command Dashboards...
echo        Hub:        http://localhost:8080
echo        Ambulance:  http://localhost:8080/ambulance.html
echo        Guardian:   http://localhost:8080/guardian.html
echo        ER Command: http://localhost:8080/er-command.html
cd /d "%~dp0"
python dashboards\serve.py
