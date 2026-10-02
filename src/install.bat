@echo off
setlocal
pushd "%~dp0.."
if errorlevel 1 goto directory_error

if exist ".venv\Scripts\python.exe" goto check_environment

set "BASE_PYTHON=python"
python -c "import sys; sys.exit(sys.version_info < (3, 13))" >nul 2>&1
if not errorlevel 1 goto create_environment

set "BASE_PYTHON=py -3"
py -3 -c "import sys; sys.exit(sys.version_info < (3, 13))" >nul 2>&1
if not errorlevel 1 goto create_environment

echo ERROR: Python 3.13 or newer must be installed and available on PATH.
goto failure

:create_environment
echo Creating the virtual environment...
%BASE_PYTHON% -m venv .venv
if errorlevel 1 goto failure

:check_environment
".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3, 13))"
if errorlevel 1 (
    echo ERROR: The virtual environment requires Python 3.13 or newer.
    goto failure
)

echo Installing ADR4agents and its dependencies...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto failure

echo Installation complete. Run start_app.bat to start the API.
set "RESULT=0"
goto finish

:failure
echo ERROR: Installation failed. Review the messages above.
set "RESULT=1"

:finish
popd
if /I not "%~1"=="--no-pause" pause
exit /b %RESULT%

:directory_error
echo ERROR: Cannot access the project directory.
if /I not "%~1"=="--no-pause" pause
exit /b 1
