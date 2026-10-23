@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0p40\windows\autostart.ps1" %*
set "strata_exit=%errorlevel%"
if not "%strata_exit%"=="0" pause
exit /b %strata_exit%
