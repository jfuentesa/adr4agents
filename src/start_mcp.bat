@echo off
setlocal
pushd "%~dp0.."
if errorlevel 1 goto directory_error

if not exist ".venv\Scripts\python.exe" goto install
".venv\Scripts\python.exe" -c "from mcp.server import MCPServer; import src.mcp_server" >nul 2>&1
if errorlevel 1 goto install
goto run

:install
call "src\install.bat" --no-pause 1>&2
if errorlevel 1 goto failure

:run
".venv\Scripts\python.exe" -m src.mcp_server %*
set "RESULT=%ERRORLEVEL%"
popd
exit /b %RESULT%

:failure
popd
exit /b 1

:directory_error
echo ERROR: Cannot access the project directory. 1>&2
exit /b 1
