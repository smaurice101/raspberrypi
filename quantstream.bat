@echo off
if not exist "C:\quantstream" mkdir "C:\quantstream"
cd /d C:\quantstream

:: --- CONFIGURABLE VARIABLES ---
:: Get Free Finnhub token from finnhub.io
set FINNHUBTOKEN=<Enter Finnhub token> 
:: If QSTEST=2 then production - if QSTEST=1 then test mode
set QSTEST=2

echo [1/6] Configuring WSL resources and idle timeout...
powershell -Command "Set-Content -Path \"$env:USERPROFILE\.wslconfig\" -Value \"[wsl2]`nvmIdleTimeout=-1`nmemory=8GB`nprocessors=4\"; Write-Host '.wslconfig updated successfully.'"

echo [2/6] Ensuring WSL is awake and responsive...
wsl --exec echo WSL is active. >nul 2>&1

echo [3/6] Waiting for Docker daemon inside WSL to become fully responsive...
:waitloop
wsl docker info >nul 2>&1
if errorlevel 1 (
    echo Docker not ready yet, retrying in 2 seconds...
    timeout /t 2 /nobreak >nul
    goto waitloop
)

echo [4/6] Cleaning up any old QuantStream containers...
wsl docker rm -f quantstream-3f10-ml >nul 2>&1

echo [5/6] Flushing lingering network/socket locks...
wsl pkill -f docker-proxy >nul 2>&1

echo [6/6] Launching QuantStream Docker container...
wsl bash -c "docker run -d --name quantstream-3f10-ml -p 5050:5050 -p 4040:4040 -p 6060:6060 --env TSS=0 --env SOLUTIONNAME=quantstream-3f10-ml --env SOLUTIONDAG=solution_preprocessing_ml_dag-quantstream-3f10 --env GITUSERNAME= --env GITPASSWORD= --env GITREPOURL='https://github.com/smaurice101/raspberrypitss.git' --env SOLUTIONEXTERNALPORT=5050 -v /var/run/docker.sock:/var/run/docker.sock:z -v /mnt/c/quantstream/tml-airflow/rawdata:/rawdata:z --env CHIP=amd64 --env SOLUTIONAIRFLOWPORT=4040 --env SOLUTIONVIPERVIZPORT=6060 --env DOCKERUSERNAME= --env EXTERNALPORT=39399 --env KAFKABROKERHOST=127.0.0.1:9092 --env KAFKACLOUDUSERNAME='<Enter API key>' --env KAFKACLOUDPASSWORD='<Enter API secret>' --env SASLMECHANISM=PLAIN --env VIPERVIZPORT=9689 --env MQTTUSERNAME= --env MQTTPASSWORD= --env AIRFLOWPORT=9000 --env READTHEDOCS= --env FINNHUBTOKEN='%FINNHUBTOKEN%' --env QSTEST=%QSTEST% --env MAXSTOCKS=50 maadsdocker/quantstream-3f10-ml-amd64-public:latest"

echo Done! Container successfully deployed.
exit
