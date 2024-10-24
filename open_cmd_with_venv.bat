@echo off

REM Path to your project
set PROJECT_PATH=D:\xxx\xxx

REM Name of your virtual environment
set VENV_NAME=venv

REM Change to the project directory
cd /d %PROJECT_PATH%

REM Activate the virtual environment
call %VENV_NAME%\Scripts\activate.bat

REM Keep the Command Prompt open
cmd