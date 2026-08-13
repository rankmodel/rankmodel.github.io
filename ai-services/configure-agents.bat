@echo off
cd %~dp0
echo Configuring AI Agent Environments...
set BASE_DIR=%cd%

:: 1. Claude Desktop
set CLAUDE_DIR=%APPDATA%\Claude
if not exist "%CLAUDE_DIR%" mkdir "%CLAUDE_DIR%"
set CLAUDE_CONF=%CLAUDE_DIR%\claude_desktop_config.json
if not exist "%CLAUDE_CONF%" (
    echo {"mcpServers": {}} > "%CLAUDE_CONF%"
)
echo Generating Claude MCP config to %CLAUDE_CONF%.new
echo { > "%CLAUDE_CONF%.new"
echo   "mcpServers": { >> "%CLAUDE_CONF%.new"
echo     "codebase-memory": { >> "%CLAUDE_CONF%.new"
echo       "command": "python", >> "%CLAUDE_CONF%.new"
echo       "args": ["%BASE_DIR%\codebase-memory-mcp\server.py"] >> "%CLAUDE_CONF%.new"
echo     } >> "%CLAUDE_CONF%.new"
echo   } >> "%CLAUDE_CONF%.new"
echo } >> "%CLAUDE_CONF%.new"

:: 2. Cursor
set CURSOR_CONF=..\.cursorrules
if not exist "%CURSOR_CONF%" (
    echo Importing ponytail rules ^& DB config for Cursor...
    echo # Cursor Rules > "%CURSOR_CONF%"
    echo IMPORT "%BASE_DIR%\ponytail\rules.md" >> "%CURSOR_CONF%"
    echo MCP_SERVER_DB "%BASE_DIR%\data\memory.db" >> "%CURSOR_CONF%"
) else (
    echo Cursor config already exists. Skipping.
)

:: 3. Windsurf
set WINDSURF_CONF=..\.windsurfrules
if not exist "%WINDSURF_CONF%" (
    echo Importing ponytail rules ^& DB config for Windsurf...
    echo # Windsurf Rules > "%WINDSURF_CONF%"
    echo IMPORT "%BASE_DIR%\ponytail\rules.md" >> "%WINDSURF_CONF%"
    echo MCP_SERVER_DB "%BASE_DIR%\data\memory.db" >> "%WINDSURF_CONF%"
) else (
    echo Windsurf config already exists. Skipping.
)

:: 4. Cline
set CLINE_DIR=..\.vscode
if not exist "%CLINE_DIR%" mkdir "%CLINE_DIR%"
set CLINE_CONF=%CLINE_DIR%\cline_mcp.json
if not exist "%CLINE_CONF%" (
    echo Generating Cline config...
    echo { > "%CLINE_CONF%"
    echo   "mcpServers": { >> "%CLINE_CONF%"
    echo     "memory": { >> "%CLINE_CONF%"
    echo       "command": "python", >> "%CLINE_CONF%"
    echo       "args": ["%BASE_DIR%\codebase-memory-mcp\server.py"] >> "%CLINE_CONF%"
    echo     } >> "%CLINE_CONF%"
    echo   } >> "%CLINE_CONF%"
    echo } >> "%CLINE_CONF%"
) else (
    echo Cline config already exists. Skipping.
)

:: 5. Generic
set GENERIC_CONF=gemini-context.json
if not exist "%GENERIC_CONF%" (
    echo Generating Generic Gemini config...
    echo { > "%GENERIC_CONF%"
    echo   "system_instructions": "You are connected to a codebase memory graph.", >> "%GENERIC_CONF%"
    echo   "endpoint": "%BASE_DIR%\data\memory.db" >> "%GENERIC_CONF%"
    echo } >> "%GENERIC_CONF%"
) else (
    echo Generic config already exists. Skipping.
)

echo Done!
