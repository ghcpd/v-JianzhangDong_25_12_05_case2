@echo off
if "%1"=="" (
  echo Usage: %~nx0 ^<path-to-module^>
  exit /b 2
)
set TARGET_MODULE=%1
python -m pytest -q tests/test_inputs.py
