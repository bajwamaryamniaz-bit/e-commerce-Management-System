@echo off
title E-Commerce DBMS Management System
cd /d "%~dp0"
echo ========================================================
echo   Starting E-Commerce DBMS Application with AI Assistant...
echo ========================================================
echo.
echo Opening browser at http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000
echo.
python run.py
pause
