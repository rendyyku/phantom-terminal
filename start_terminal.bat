@echo off
title Phantom Terminal 2.0 Launcher
color 0B

echo ===================================================
echo     PHANTOM TERMINAL: NEXT-GEN AI QUANT ^& MT5      
echo ===================================================
echo [1/2] Launching Python Core Engine (FastAPI)...

cd phantom-core
start /b python server.py

timeout /t 2 /nobreak >nul

echo [2/2] Opening Cyberpunk Terminal UI in Browser...
start http://127.0.0.1:8000

echo.
echo [OK] Phantom Terminal is running!
echo UI URL: http://127.0.0.1:8000
echo MT5 Port: 9988
echo.
pause
