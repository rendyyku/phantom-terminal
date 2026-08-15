@echo off
title Phantom Terminal 2.0 Launcher
color 0B

echo ===================================================
echo     PHANTOM TERMINAL: NEXT-GEN AI QUANT ^& MT5      
echo ===================================================
echo [1/3] Checking ^& freeing ports 8000 and 9988...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":9988" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Launching Python Core Engine (FastAPI)...
cd phantom-core
start /b python server.py

timeout /t 2 /nobreak >nul

echo [3/3] Opening Terminal UI in Browser...
start http://127.0.0.1:8000

echo.
echo [OK] Phantom Terminal is running cleanly!
echo UI URL: http://127.0.0.1:8000
echo MT5 Port: 9988
echo.
pause
