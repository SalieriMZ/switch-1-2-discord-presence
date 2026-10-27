@echo off
rem Compila la app en dist\NSO-Discord-RPC\ (doble clic).
rem   compilar.bat         compilacion rapida (incremental)
rem   compilar.bat -Zip    ademas crea el .zip para compartir
rem   compilar.bat -Clean  desde cero
cd /d "%~dp0"

tasklist /FI "IMAGENAME eq NSO-Discord-RPC.exe" /NH | find /I "NSO-Discord-RPC.exe" >nul
if not errorlevel 1 (
    echo Cerrando NSO-Discord-RPC para poder reemplazar sus archivos...
    taskkill /IM NSO-Discord-RPC.exe /F >nul
    timeout /t 1 /nobreak >nul
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build\build.ps1" %*
if errorlevel 1 (
    echo.
    echo *** La compilacion fallo. Revisa el mensaje de arriba. ***
    pause
    exit /b 1
)
echo.
echo Abre: dist\NSO-Discord-RPC\NSO-Discord-RPC.exe
pause
