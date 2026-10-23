@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0p40\windows\launch-strata.ps1"
if errorlevel 1 pause
