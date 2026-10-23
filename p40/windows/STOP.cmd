@echo off
setlocal
cd /d "%~dp0"
"%~dp0runtime\python\python.exe" -I -s -B "%~dp0tools\service-lifecycle.py" --stop
if errorlevel 1 pause
