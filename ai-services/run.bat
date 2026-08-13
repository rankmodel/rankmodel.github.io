@echo off
REM run.bat
REM Starts AI services on demand

set SERVICE=%1

if "%SERVICE%"=="" (
    echo Usage: run.bat ^<service_name^>
    echo Available services:
    echo   - ponytail
    echo   - notebooklm-py
    echo   - prompt-master
    echo   - codebase-memory-mcp
    echo   - caveman
    echo   - ai-specs
    echo   - guide
    echo   - agent-rules
    echo   - prompt-optimizer
    echo   - textgrad
    echo   - Trace
    echo   - awesome-ai-agents-2026
    echo   - junior-to-senior
    echo   - grill-me
    echo   - interface-kit
    exit /b 1
)

if exist "%SERVICE%\" (
    echo Starting %SERVICE%...
    REM Mock startup script
    echo %SERVICE% is now running ^(mock^).
) else (
    echo Service '%SERVICE%' not found.
    exit /b 1
)
