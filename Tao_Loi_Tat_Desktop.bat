@echo off
chcp 65001 >nul
title Tao Loi Tat TS Origin Mobile App Ra Desktop
echo ============================================================
echo   DANG TAO HOAC CAP NHAT LOI TAT RA MAN HINH DESKTOP...
echo ============================================================
echo.

set "CURRENT_DIR=%~dp0"
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

set "VBS_FILE=%CURRENT_DIR%\launch_app.vbs"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT_PATH=%DESKTOP_DIR%\TS Origin Mobile App.lnk"

REM Tu dong chon icon hop ly (Chrome -> Edge -> TS_Origin_Control.exe)
set "ICON_LOC=%CURRENT_DIR%\TS_Origin_Control.exe,0"
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "ICON_LOC=C:\Program Files\Google\Chrome\Application\chrome.exe,0"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "ICON_LOC=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe,0"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    set "ICON_LOC=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe,0"
)

(
echo Set oWS = CreateObject("WScript.Shell"^)
echo Set oLink = oWS.CreateShortcut("%SHORTCUT_PATH%"^)
echo oLink.TargetPath = "wscript.exe"
echo oLink.Arguments = """%VBS_FILE%"""
echo oLink.WorkingDirectory = "%CURRENT_DIR%"
echo oLink.IconLocation = "%ICON_LOC%"
echo oLink.Description = "TS Origin Mobile App 1-Click"
echo oLink.Save
) > "%TEMP%\_create_sc.vbs"

cscript //nologo "%TEMP%\_create_sc.vbs"
if exist "%TEMP%\_create_sc.vbs" del "%TEMP%\_create_sc.vbs"

echo [OK] Thu muc hien tai: %CURRENT_DIR%
echo [OK] Da tao thanh cong bieu tuong tai:
echo      %SHORTCUT_PATH%
echo.
echo ============================================================
echo   HOAN TAT! TU NAY BAN CO THE MO APP TRUC TIEP TU DESKTOP!
echo ============================================================
ping 127.0.0.1 -n 2 >nul
exit
