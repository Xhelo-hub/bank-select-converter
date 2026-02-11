@echo off
REM Quick deploy script - runs the PowerShell deployment
powershell -ExecutionPolicy Bypass -File "%~dp0deploy.ps1" %*
