@echo off
REM ===========================================================================
REM  Stop the AirLLM Gateway services started by Start-AirLLM.bat.
REM
REM  Only AirLLM-OWNED processes are touched. The backend/dashboard are matched
REM  by the distinctive window titles Start-AirLLM.bat gives them ("AirLLM
REM  Backend" / "AirLLM Dashboard"), never by port - so an unrelated service
REM  that happens to use :4000 or :3000 is left untouched.
REM
REM  Usage:
REM    Stop-AirLLM.bat                  stop backend + dashboard + Postgres
REM    Stop-AirLLM.bat --services-only  stop backend + dashboard, keep Postgres
REM ===========================================================================
setlocal EnableExtensions

set "SERVICES_ONLY=0"
for %%A in (%*) do (
  if /i "%%~A"=="--services-only" set "SERVICES_ONLY=1"
)

echo Stopping AirLLM Gateway services...

REM Close the spawned backend/dashboard windows (and their child trees) by their
REM AirLLM-owned titles. taskkill returns non-zero when nothing matches.
taskkill /fi "WINDOWTITLE eq AirLLM Backend*" /t /f >nul 2>nul && (echo   - Backend stopped.) || (echo   - Backend was not running.)
taskkill /fi "WINDOWTITLE eq AirLLM Dashboard*" /t /f >nul 2>nul && (echo   - Dashboard stopped.) || (echo   - Dashboard was not running.)

if "%SERVICES_ONLY%"=="1" (
  endlocal & exit /b 0
)

REM Stop the AirLLM-owned Postgres container (data volume is preserved).
where docker >nul 2>nul && (
  docker stop airllm-pg >nul 2>nul && (echo   - Postgres container stopped.) || (echo   - Postgres container was not running.)
)

echo Done.
endlocal & exit /b 0
