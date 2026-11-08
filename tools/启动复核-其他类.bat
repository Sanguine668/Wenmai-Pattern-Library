@echo off
cd /d "%~dp0.."
where python >nul 2>nul
if %errorlevel%==0 (
  python tools\start_task.py other
) else (
  py -3 tools\start_task.py other
)
pause
