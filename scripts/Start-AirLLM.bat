@echo off
docker compose up -d
pause

REM Wait for the daemon to become available.
set /a "_retries=15"
:ensure_docker_daemon_wait
docker info >nul 2>nul
if not errorlevel 1 exit /b 0
set /a "_retries-=_1"
if !_retries! LEQ 0 exit /b 1
call :sleep 2
goto :ensure_docker_daemon_wait

:start_docker_desktop
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
  echo [AirLLM] Docker daemon unavailable; launching Docker Desktop...
  start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  exit /b 0
)
if exist "%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe" (
  echo [AirLLM] Docker daemon unavailable; launching Docker Desktop...
  start "" "%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe"
  exit /b 0
)
exit /b 1

:port_listening
REM %1 = TCP port. Returns errorlevel 0 when a process is LISTENING on it.
netstat -ano -p tcp 2>nul | findstr "LISTENING" | findstr /C:":%~1 " >nul 2>nul
exit /b

:http_status
REM %1 = URL. Sets HTTP_STATUS to the numeric HTTP code, or 000 if unreachable.
set "HTTP_STATUS=000"
where curl >nul 2>nul
if errorlevel 1 goto :http_status_ps
for /f "usebackq delims=" %%i in (`curl -s -o nul -w "%%{http_code}" --max-time 3 "%~1" 2^>nul`) do set "HTTP_STATUS=%%i"
exit /b
:http_status_ps
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "try{(Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 3).StatusCode}catch{if($_.Exception.Response){[int]$_.Exception.Response.StatusCode}else{'000'}}" 2^>nul`) do set "HTTP_STATUS=%%i"
exit /b

:wait_port
REM %1 = port, %2 = max attempts (~seconds). errorlevel 0 once it is LISTENING.
set /a "_wp=%~2"
:wait_port_loop
call :port_listening %~1
if not errorlevel 1 exit /b 0
set /a "_wp-=1"
if !_wp! LEQ 0 exit /b 1
call :sleep 1
goto :wait_port_loop

:ensure_backend
REM Decide whether to start the backend or reuse a running one.
call :port_listening 4000
if errorlevel 1 goto :backend_start
REM Port 4000 is occupied - is it a healthy AirLLM backend?
call :http_status "http://127.0.0.1:4000/health"
if "!HTTP_STATUS!"=="200" (
  echo [AirLLM] Backend already running on port 4000.
  set "BACKEND_ACTION=reused"
  exit /b 0
)
echo [WARN] Port 4000 is in use but not a healthy AirLLM backend ^(/health=!HTTP_STATUS!^).
echo [WARN] Skipping backend start to avoid a bind conflict; use --restart to replace it.
set "BACKEND_ACTION=conflict"
exit /b 0
:backend_start
echo Starting gateway backend on :4000 ...
start "AirLLM Backend" /d "%ROOT%\backend" cmd /k ".venv\Scripts\alembic.exe upgrade head && .venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 4000"
set "BACKEND_ACTION=started"
exit /b 0

:ensure_dashboard
REM Decide whether to start the dashboard or reuse a running one.
call :port_listening 3000
if errorlevel 1 goto :dashboard_start
echo [AirLLM] Dashboard already running on port 3000.
set "DASHBOARD_ACTION=reused"
exit /b 0
:dashboard_start
echo Starting dashboard on :3000 ...
start "AirLLM Dashboard" /d "%ROOT%\frontend" cmd /k "npm run dev"
set "DASHBOARD_ACTION=started"
exit /b 0

:print_status
set "BACKEND_STATE=Not running"
call :port_listening 4000
if not errorlevel 1 set "BACKEND_STATE=Running (port 4000)"
if "%BACKEND_ACTION%"=="started" if "%BACKEND_STATE%"=="Not running" set "BACKEND_STATE=Starting (port 4000)"
if "%BACKEND_ACTION%"=="conflict" set "BACKEND_STATE=Port 4000 busy (foreign process)"

set "DASH_STATE=Not running"
call :port_listening 3000
if not errorlevel 1 set "DASH_STATE=Running (port 3000)"
if "%DASHBOARD_ACTION%"=="started" if "%DASH_STATE%"=="Not running" set "DASH_STATE=Starting (port 3000)"

set "DB_STATE=Not connected"
call :port_listening 5432
if not errorlevel 1 set "DB_STATE=Connected"

echo.
echo ====================================
echo  AirLLM Startup Status
echo ====================================
echo Backend   : %BACKEND_STATE%
echo Dashboard : %DASH_STATE%
echo Database  : %DB_STATE%
echo ====================================
echo.
echo    Dashboard : http://localhost:3000
echo    Gateway   : http://localhost:4000
echo    API docs  : http://localhost:4000/docs
echo.
echo    Stop    : scripts\Stop-AirLLM.bat
echo    Restart : scripts\Start-AirLLM.bat --restart
exit /b 0
