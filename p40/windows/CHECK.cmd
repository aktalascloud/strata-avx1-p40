@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0p40\windows\prerequisites.ps1" -CheckOnly
if errorlevel 1 goto failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0p40\windows\launch-strata.ps1" -CheckOnly
if errorlevel 1 goto failed
echo Package verified. No model downloaded, server started or task registered.
pause
exit /b 0
:failed
echo Package or prerequisite check failed.
pause
exit /b 1
