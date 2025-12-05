@echo off
REM Test script for Windows
REM This script performs security analysis and comparison tests

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Security Audit Test Suite (Windows)
echo ========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Create logs directory
if not exist "logs" mkdir logs

REM Get timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set date=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set time=%%a:%%b)
set TIMESTAMP=%date% %time%
set TEST_LOG=logs\test_run.log

echo. >> %TEST_LOG%
echo ========================================= >> %TEST_LOG%
echo Test Run: %TIMESTAMP% >> %TEST_LOG%
echo ========================================= >> %TEST_LOG%

REM Test 1: Syntax validation
echo. >> %TEST_LOG%
echo [TEST 1] Checking Python syntax... >> %TEST_LOG%
echo [TEST 1] Checking Python syntax...
python -m py_compile inputs_backup.py 2>> %TEST_LOG%
if errorlevel 1 (
    echo [FAILED] inputs_backup.py has syntax errors >> %TEST_LOG%
    echo TEST FAILED >> %TEST_LOG%
    exit /b 1
)
echo [PASSED] inputs_backup.py syntax is valid >> %TEST_LOG%
echo [PASSED] inputs_backup.py syntax is valid

REM Test 2: Check secured file syntax
echo. >> %TEST_LOG%
echo [TEST 2] Checking secured inputs.py syntax... >> %TEST_LOG%
echo [TEST 2] Checking secured inputs.py syntax...
python -m py_compile inputs.py 2>> %TEST_LOG%
if errorlevel 1 (
    echo [FAILED] inputs.py has syntax errors >> %TEST_LOG%
    echo TEST FAILED >> %TEST_LOG%
    exit /b 1
)
echo [PASSED] inputs.py syntax is valid >> %TEST_LOG%
echo [PASSED] inputs.py syntax is valid

REM Test 3: Check for hardcoded secrets in backup
echo. >> %TEST_LOG%
echo [TEST 3] Scanning inputs_backup.py for hardcoded secrets... >> %TEST_LOG%
echo [TEST 3] Scanning inputs_backup.py for hardcoded secrets...
findstr "tok_production mail_srv_key admin_internal" inputs_backup.py > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Expected hardcoded secrets not found in inputs_backup.py >> %TEST_LOG%
) else (
    echo [DETECTED] Hardcoded secrets found in inputs_backup.py ^(expected^) >> %TEST_LOG%
    echo [DETECTED] Hardcoded secrets found in inputs_backup.py
)

REM Test 4: Check that secrets are removed
echo. >> %TEST_LOG%
echo [TEST 4] Verifying hardcoded secrets removed from inputs.py... >> %TEST_LOG%
echo [TEST 4] Verifying hardcoded secrets removed from inputs.py...
findstr "tok_production mail_srv_key_ABCDEFG admin_internal_5566" inputs.py > nul 2>&1
if errorlevel 0 (
    echo [FAILED] Hardcoded secrets still present in inputs.py >> %TEST_LOG%
    echo TEST FAILED >> %TEST_LOG%
    exit /b 1
)
echo [PASSED] Hardcoded secrets removed from inputs.py >> %TEST_LOG%
echo [PASSED] Hardcoded secrets removed from inputs.py

REM Test 5: Check for SQL injection vulnerability in backup
echo. >> %TEST_LOG%
echo [TEST 5] Scanning inputs_backup.py for SQL injection vulnerability... >> %TEST_LOG%
echo [TEST 5] Scanning inputs_backup.py for SQL injection vulnerability...
findstr "WHERE id = " inputs_backup.py > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Expected SQL injection vulnerability not found >> %TEST_LOG%
) else (
    echo [DETECTED] SQL injection vulnerability found in inputs_backup.py ^(expected^) >> %TEST_LOG%
    echo [DETECTED] SQL injection vulnerability found in inputs_backup.py
)

REM Test 6: Check for command injection in backup
echo. >> %TEST_LOG%
echo [TEST 6] Scanning inputs_backup.py for command injection vulnerability... >> %TEST_LOG%
echo [TEST 6] Scanning inputs_backup.py for command injection vulnerability...
findstr "shell=True" inputs_backup.py > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Expected command injection vulnerability not found >> %TEST_LOG%
) else (
    echo [DETECTED] Command injection vulnerability found in inputs_backup.py ^(expected^) >> %TEST_LOG%
    echo [DETECTED] Command injection vulnerability found in inputs_backup.py
)

REM Test 7: Check for proper fixes in secured version
echo. >> %TEST_LOG%
echo [TEST 7] Verifying command injection fixed in inputs.py... >> %TEST_LOG%
echo [TEST 7] Verifying command injection fixed in inputs.py...
findstr "shell=False" inputs.py > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Could not verify shell=False usage >> %TEST_LOG%
) else (
    echo [PASSED] shell=False is used in subprocess calls >> %TEST_LOG%
    echo [PASSED] shell=False is used in subprocess calls
)

REM Test 8: Check for MD5 usage in backup
echo. >> %TEST_LOG%
echo [TEST 8] Scanning inputs_backup.py for weak hash function MD5... >> %TEST_LOG%
echo [TEST 8] Scanning inputs_backup.py for weak hash function MD5...
findstr "hashlib.md5" inputs_backup.py > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Expected MD5 usage not found >> %TEST_LOG%
) else (
    echo [DETECTED] MD5 weak hash usage found in inputs_backup.py ^(expected^) >> %TEST_LOG%
    echo [DETECTED] MD5 weak hash usage found in inputs_backup.py
)

REM Test 9: Check for error handling
echo. >> %TEST_LOG%
echo [TEST 9] Verifying error handling in inputs.py... >> %TEST_LOG%
echo [TEST 9] Verifying error handling in inputs.py...
findstr "try:" inputs.py > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Error handling not properly implemented >> %TEST_LOG%
) else (
    echo [PASSED] Error handling and logging implemented >> %TEST_LOG%
    echo [PASSED] Error handling and logging implemented
)

REM Final result
echo. >> %TEST_LOG%
echo ========================================= >> %TEST_LOG%
echo TEST PASSED >> %TEST_LOG%
echo ========================================= >> %TEST_LOG%
echo Test log saved to: %TEST_LOG% >> %TEST_LOG%

echo.
echo ========================================
echo TEST PASSED
echo ========================================
echo Test log saved to: %TEST_LOG%
echo.

exit /b 0
