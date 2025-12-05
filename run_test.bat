@echo off
REM Usage: run_test.bat <file> <vulnerable|secure>
setlocal
if "%~1"=="" (
  set FILE=input.py
) else (
  set FILE=%~1
)
if "%~2"=="" (
  set MODE=secure
) else (
  set MODE=%~2
)
python -u test_runner.py "%FILE%" "%MODE%"
exit /b %errorlevel%
