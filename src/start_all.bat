@echo off
setlocal
pushd "%~dp0.."
if errorlevel 1 goto directory_error

if not exist ".venv\Scripts\python.exe" goto install
".venv\Scripts\python.exe" -c "import sys, flask, waitress; from mcp.server import MCPServer; import src.mcp_server; sys.exit(sys.version_info < (3, 13))" >nul 2>&1
if errorlevel 1 goto install
goto run

:install
call "src\install.bat" --no-pause
if errorlevel 1 goto failure

:run
start "ADR4agents - Web and API" /D "%~dp0" "%ComSpec%" /d /k call start_app.bat
if errorlevel 1 goto failure
start "ADR4agents - MCP" /D "%~dp0" "%ComSpec%" /d /k call start_mcp.bat
if errorlevel 1 goto failure
echo Startup requested in two separate windows. Press Ctrl+C in each window to stop its server.
popd
exit /b 0

:failure
echo ERROR: Setup or launching a server window failed. Review any open server windows.
popd
if not defined ADR4AGENTS_NO_PAUSE pause
exit /b 1

:directory_error
echo ERROR: Cannot access the project directory.
if not defined ADR4AGENTS_NO_PAUSE pause
exit /b 1
