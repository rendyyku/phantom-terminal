Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    PHANTOM TERMINAL: NEXT-GEN AI QUANT & MT5      " -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/2] Starting Phantom Core Engine (FastAPI & WebSocket)..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "server.py" -WorkingDirectory "$scriptDir\phantom-core" -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "[2/2] Opening Cyberpunk Terminal UI in Default Browser..." -ForegroundColor Green
$uiPath = "$scriptDir\terminal-ui\index.html"
Start-Process $uiPath

Write-Host "`n[OK] Phantom Terminal is now active!" -ForegroundColor Cyan
Write-Host "Core URL: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "MT5 Socket: 127.0.0.1:9988" -ForegroundColor White
