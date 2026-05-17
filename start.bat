@echo off
powershell -NoLogo -ExecutionPolicy RemoteSigned -File "%~dp0start.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   Error al ejecutar el launcher.
    pause
)
