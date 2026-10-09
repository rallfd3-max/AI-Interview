@echo off
cd /d "%~dp0Redis-x64-3.0.504"
redis-server.exe redis.windows.conf
pause