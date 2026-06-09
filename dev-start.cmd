@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ops\scripts\dev-start.ps1" %*
