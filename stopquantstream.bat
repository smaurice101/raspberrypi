@echo off
cd /d C:\maads

echo [1/3] Stopping and removing QuantStream Docker container...
wsl docker rm -f quantstream-3f10-ml >nul 2>&1
echo Container stopped and removed.

echo [2/3] Cleaning up lingering Docker proxy processes...
wsl pkill -f docker-proxy >nul 2>&1

echo [3/3] Shutting down WSL to release system memory...
REM wsl --shutdown

echo QuantStream environment successfully stopped and cleaned up!
exit