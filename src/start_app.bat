@echo off
setlocal
pushd "%~dp0.."
if errorlevel 1 goto directory_error

if not exist ".venv\Scripts\python.exe" goto install
".venv\Scripts\python.exe" -c "import sys, flask, waitress; sys.exit(sys.version_info < (3, 13))" >nul 2>&1
if errorlevel 1 goto install
goto run

:install
call "src\install.bat" --no-pause
if errorlevel 1 goto failure

:run
echo Starting ADR4agents with Waitress. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m src %*
set "RESULT=%ERRORLEVEL%"
popd
if not "%RESULT%"=="0" (
    echo ERROR: Application startup or execution failed.
    if not defined ADR4AGENTS_NO_PAUSE pause
)
exit /b %RESULT%

:failure
popd
if not defined ADR4AGENTS_NO_PAUSE pause
exit /b 1

:directory_error
echo ERROR: Cannot access the project directory.
if not defined ADR4AGENTS_NO_PAUSE pause
exit /b 1
