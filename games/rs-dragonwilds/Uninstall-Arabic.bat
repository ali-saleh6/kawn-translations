@echo off
rem Double-click to remove the Arabic patch and return to the stock game text.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Arabic.ps1" -Uninstall
pause
