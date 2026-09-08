@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SonarDeck Studio Release
cd /d "%~dp0.."

echo ========================================
echo SonarDeck Studio Release
echo Project: %cd%
echo ========================================
echo.
echo 1) Run this on the bridge/server PC.
echo 2) Keep this window open.
echo 3) On another device, use the LAN/tunnel URL printed below.
echo.
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Python was not found on PATH.
  echo Install Python 3.11+ and ensure Add to PATH is enabled.
  echo.
  pause
  exit /b 1
)

if not exist "bridge\config.json" (
  echo Creating bridge\config.json from bridge\config.example.json...
  copy "bridge\config.example.json" "bridge\config.json" >nul
)

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$configs = Get-NetIPConfiguration ^| Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq 'Up' -and $_.InterfaceAlias -notmatch 'vEthernet|VMware|Virtual|Loopback|Tailscale|Hyper-V' }; if ($configs.Count -gt 0) { $ip = $configs[0].IPv4Address.IPAddress } else { $ip = (Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254*' } ^| Select-Object -First 1 -ExpandProperty IPAddress) }; if (-not $ip) { $ip = '127.0.0.1' }; $ip"`) do set "LAN_IP=%%I"
if not defined LAN_IP set "LAN_IP=127.0.0.1"
set "LAN_URL=http://%LAN_IP%:8766"

net session >nul 2>nul
if errorlevel 1 (
  echo Admin permission is required once to open port 8766 in Windows Firewall.
  echo Approve the UAC prompt, then run the launcher again if needed.
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (-not (Get-NetFirewallRule -DisplayName 'SonarDeck Studio Release 8766' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -DisplayName 'SonarDeck Studio Release 8766' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8766 | Out-Null }"

echo Stopping any old SonarDeck listeners on port 8766...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8766 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul

echo Starting release server on %LAN_URL% ...
echo This PC is the bridge/server. On a gaming PC, tablet, or phone, open the bridge/server URL shown below - do not use 127.0.0.1 on another device.
echo Bridge/server URL: %LAN_URL%
start "SonarDeck Release" cmd /k "cd /d ""%cd%"" && %PYTHON_CMD% -m bridge.web_api --host 0.0.0.0 --port 8766"

timeout /t 3 >nul
start "" "%LAN_URL%"

echo.
echo Local PC URL: %LAN_URL%
echo If another device cannot connect, confirm it is on the same Wi-Fi/LAN subnet as this PC.
echo If it is on guest Wi-Fi or a different subnet, use Tailscale or a Cloudflare tunnel instead.
echo.
pause
