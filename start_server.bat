@echo off
cd /d C:\dev\pickup-market

start "Django Server" powershell -NoExit -Command ".\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000"

timeout /t 5 >nul

start "Public Tunnel" powershell -NoExit -Command "cloudflared tunnel --url http://localhost:8000 --allowed-mail songhyunoh@naver.com"