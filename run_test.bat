@echo off
if "%1"=="" (
  set FILE=inputs.py
) else (
  set FILE=%1
)
python -m tests.run_tests "%FILE%"
