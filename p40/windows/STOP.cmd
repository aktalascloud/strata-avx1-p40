@echo off
setlocal
cd /d "%~dp0"
"%~dp0runtime\python\python.exe" -I -s -B "%~dp0tools\service-lifecycle.py" --stop
set "strata_exit=%errorlevel%"
if not "%strata_exit%"=="0" pause
exit /b %strata_exit%
