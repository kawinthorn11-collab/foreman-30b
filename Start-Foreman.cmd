@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "..\HuaNaNgan\runtime\python\python.exe" (
  "..\HuaNaNgan\runtime\python\python.exe" -X utf8 scripts\project.py interactive
) else (
  python -X utf8 scripts\project.py interactive
)
pause
