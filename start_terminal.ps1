Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    PHANTOM TERMINAL: NEXT-GEN AI QUANT & MT5      " -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/3] Checking & clearing existing instances on ports 8000 and 9988..." -ForegroundColor DarkGray
Get-NetTCPConnection -LocalPort 8000, 9988 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host "[2/3] Starting Phantom Core Engine (FastAPI & WebSocket)..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "server.py" -WorkingDirectory "$scriptDir\phantom-core" -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "[3/3] Opening Terminal UI at http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

Write-Host "`n[OK] Phantom Terminal is now active!" -ForegroundColor Cyan
Write-Host "Core URL: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "MT5 Socket: 127.0.0.1:9988" -ForegroundColor White
