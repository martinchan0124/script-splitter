@echo off
cd /d "%~dp0\..\.."
set PYTHONPATH=%CD%
start pythonw app\gui.py
