@echo off
cd /d D:\HOANGVU\VPS\TwinSelf
title Portfolio Server - Port 8080
echo Starting Portfolio Server...
uvicorn portfolio_server:app --host 0.0.0.0 --port 8080 --workers 1
pause
