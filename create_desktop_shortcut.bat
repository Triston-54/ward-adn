@echo off
setlocal EnableExtensions DisableDelayedExpansion

title Create The Ward Desktop Shortcut
cd /d "%~dp0"

echo.
echo  Creating a desktop shortcut for The Ward...
echo.

set "LAUNCHER=%~dp0launch_ward.bat"
set "ICON=%~dp0static\images\ward-icon-512.png"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\The Ward.lnk"

if not exist "%LAUNCHER%" (
    echo  [ERROR] launch_ward.bat was not found in this folder.
    echo  Expected: %LAUNCHER%
    echo.
    pause
    exit /b 1
)

set "WARD_LAUNCHER=%LAUNCHER%"
set "WARD_ICON=%ICON%"
set "WARD_SHORTCUT=%SHORTCUT%"

powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABsAGEAdQBuAGMAaABlAHIAPQAkAGUAbgB2ADoAVwBBAFIARABfAEwAQQBVAE4AQwBIAEUAUgAKACQAaQBjAG8AbgA9ACQAZQBuAHYAOgBXAEEAUgBEAF8ASQBDAE8ATgAKACQAcwBoAG8AcgB0AGMAdQB0AD0AJABlAG4AdgA6AFcAQQBSAEQAXwBTAEgATwBSAFQAQwBVAFQACgAkAHMAaABlAGwAbAA9AE4AZQB3AC0ATwBiAGoAZQBjAHQAIAAtAEMAbwBtAE8AYgBqAGUAYwB0ACAAVwBTAGMAcgBpAHAAdAAuAFMAaABlAGwAbAAKACQAbABpAG4AawA9ACQAcwBoAGUAbABsAC4AQwByAGUAYQB0AGUAUwBoAG8AcgB0AGMAdQB0ACgAJABzAGgAbwByAHQAYwB1AHQAKQAKACQAbABpAG4AawAuAFQAYQByAGcAZQB0AFAAYQB0AGgAPQAkAGwAYQB1AG4AYwBoAGUAcgAKACQAbABpAG4AawAuAFcAbwByAGsAaQBuAGcARABpAHIAZQBjAHQAbwByAHkAPQAoAFMAcABsAGkAdAAtAFAAYQB0AGgAIAAkAGwAYQB1AG4AYwBoAGUAcgAgAC0AUABhAHIAZQBuAHQAKQAKACQAbABpAG4AawAuAFcAaQBuAGQAbwB3AFMAdAB5AGwAZQA9ADEACgAkAGwAaQBuAGsALgBEAGUAcwBjAHIAaQBwAHQAaQBvAG4APQAnAEwAYQB1AG4AYwBoACAAVABoAGUAIABXAGEAcgBkACAALQAgAEEARABOACAATgB1AHIAcwBpAG4AZwAgAFMAdAB1AGQAeQAgAFMAdQBpAHQAZQAnAAoAaQBmACAAKAAkAGkAYwBvAG4AIAAtAGEAbgBkACAAKABUAGUAcwB0AC0AUABhAHQAaAAgACQAaQBjAG8AbgApACkAIAB7ACAAJABsAGkAbgBrAC4ASQBjAG8AbgBMAG8AYwBhAHQAaQBvAG4AIAA9ACAAJABpAGMAbwBuACAAKwAgACcALAAwACcAIAB9AAoAJABsAGkAbgBrAC4AUwBhAHYAZQAoACkACgBlAHgAaQB0ACAAMAA= >nul 2>&1

if errorlevel 1 goto shortcut_failed
echo   [OK] Shortcut created: %SHORTCUT%
goto shortcut_ok

:shortcut_failed
echo.
echo  [ERROR] Could not create the shortcut.
echo  Try running this file as a normal user, not from a restricted folder.
echo.
pause
exit /b 1

:shortcut_ok

echo.
echo  Done. Double-click The Ward on your desktop to start the app.
echo.
pause
exit /b 0