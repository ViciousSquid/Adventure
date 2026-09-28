@echo off
setlocal

rem Adventure launcher for Windows users.
rem No PowerShell, Windows Terminal, Python, or command prompt knowledge is required.
rem The application is served as the browser-based PWA from the pwa-pyodide branch.

set "URL=https://cdn.jsdelivr.net/gh/ViciousSquid/Adventure@pwa-pyodide/static/index.html"

start "" "%URL%"

endlocal
