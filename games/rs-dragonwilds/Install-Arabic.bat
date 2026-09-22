@echo off
rem Double-click to install the Arabic patch (Arabic replaces English).
rem For the French-slot variant run: Install-Arabic.bat French
set MODE=%1
if "%MODE%"=="" set MODE=English
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Arabic.ps1" -Mode %MODE%
pause
