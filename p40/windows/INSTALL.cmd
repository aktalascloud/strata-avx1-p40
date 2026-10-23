@echo off
setlocal
cd /d "%~dp0"
echo Strata AVX1 / Tesla P40 - portable installation
echo Read THIRD_PARTY_NOTICES.md and licenses before continuing.
echo NVIDIA components remain subject to the included NVIDIA license.
echo Model licenses apply to downloads directly from Hugging Face.
choice /C YN /N /M "Accept these terms and continue? [Y/N] "
if errorlevel 2 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0p40\windows\prerequisites.ps1"
if errorlevel 1 goto failed
"%~dp0runtime\python\python.exe" -I -s -B "%~dp0p40\windows\installer.py" %*
if errorlevel 1 goto failed
echo Installation complete. Run START.cmd.
pause
exit /b 0
:failed
echo Installation paused or failed. Partial downloads are preserved. Run INSTALL.cmd again to resume.
pause
exit /b 1
