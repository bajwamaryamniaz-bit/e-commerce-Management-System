@echo off
title Push DBMS Project to GitHub (bajwamaryamniaz-bit)
color 0b
echo ============================================================
echo   Pushing E-Commerce Management System to GitHub
echo   Target Account: bajwamaryamniaz-bit
echo   Repository: https://github.com/bajwamaryamniaz-bit/e-commerce-Management-System.git
echo ============================================================
echo.
cd /d "%~dp0"
echo Step 1: Checking Git status...
git status
echo.
echo Step 2: Pushing to GitHub (origin main)...
echo [NOTE] Abhi browser me ek pop-up ya window khulegi.
echo        Wahan bajwamaryamniaz-bit account se "Sign in" ya "Authorize" kar dein.
echo.
git push -u origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo ============================================================
    echo [SUCCESS] Mubarak ho! Tamam files bajwamaryamniaz-bit ke GitHub repo me upload ho gayi hain!
    echo Link: https://github.com/bajwamaryamniaz-bit/e-commerce-Management-System
    echo ============================================================
) else (
    echo ============================================================
    echo [ERROR] Push fail hua ya cancel hua.
    echo ============================================================
)
echo.
pause
