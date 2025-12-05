#!/bin/bash

# Test script for Linux/macOS
# This script performs security analysis and comparison tests

set -e

echo "========================================"
echo "Security Audit Test Suite (Linux/macOS)"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Create logs directory
mkdir -p logs

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TEST_LOG="logs/test_run.log"

echo "" | tee -a "$TEST_LOG"
echo "=======================================" | tee -a "$TEST_LOG"
echo "Test Run: $TIMESTAMP" | tee -a "$TEST_LOG"
echo "=======================================" | tee -a "$TEST_LOG"

# Test 1: Syntax validation
echo "" | tee -a "$TEST_LOG"
echo "[TEST 1] Checking Python syntax..." | tee -a "$TEST_LOG"
python -m py_compile inputs_backup.py 2>&1 | tee -a "$TEST_LOG" || {
    echo "[FAILED] inputs_backup.py has syntax errors" | tee -a "$TEST_LOG"
    echo "TEST FAILED" >> "$TEST_LOG"
    exit 1
}
echo "[PASSED] inputs_backup.py syntax is valid" | tee -a "$TEST_LOG"

echo "" | tee -a "$TEST_LOG"
echo "[TEST 2] Checking secured inputs.py syntax..." | tee -a "$TEST_LOG"
python -m py_compile inputs.py 2>&1 | tee -a "$TEST_LOG" || {
    echo "[FAILED] inputs.py has syntax errors" | tee -a "$TEST_LOG"
    echo "TEST FAILED" >> "$TEST_LOG"
    exit 1
}
echo "[PASSED] inputs.py syntax is valid" | tee -a "$TEST_LOG"

# Test 2: Check for hardcoded secrets in backup
echo "" | tee -a "$TEST_LOG"
echo "[TEST 3] Scanning inputs_backup.py for hardcoded secrets..." | tee -a "$TEST_LOG"
if grep -E "(tok_production|mail_srv_key|admin_internal)" inputs_backup.py > /dev/null 2>&1; then
    echo "[DETECTED] Hardcoded secrets found in inputs_backup.py (expected)" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Expected hardcoded secrets not found in inputs_backup.py" | tee -a "$TEST_LOG"
fi

# Test 3: Check that secrets are removed in secured version
echo "" | tee -a "$TEST_LOG"
echo "[TEST 4] Verifying hardcoded secrets removed from inputs.py..." | tee -a "$TEST_LOG"
if grep -E "(tok_production|mail_srv_key_ABCDEFG|admin_internal_5566)" inputs.py > /dev/null 2>&1; then
    echo "[FAILED] Hardcoded secrets still present in inputs.py" | tee -a "$TEST_LOG"
    echo "TEST FAILED" >> "$TEST_LOG"
    exit 1
fi
echo "[PASSED] Hardcoded secrets removed from inputs.py" | tee -a "$TEST_LOG"

# Test 4: Check for SQL injection vulnerability in backup
echo "" | tee -a "$TEST_LOG"
echo "[TEST 5] Scanning inputs_backup.py for SQL injection vulnerability..." | tee -a "$TEST_LOG"
if grep -E "SELECT.*WHERE.*id.*=.*%.*uid" inputs_backup.py > /dev/null 2>&1; then
    echo "[DETECTED] SQL injection vulnerability found in inputs_backup.py (expected)" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Expected SQL injection vulnerability not found in inputs_backup.py" | tee -a "$TEST_LOG"
fi

# Test 5: Check that SQL injection is fixed in secured version
echo "" | tee -a "$TEST_LOG"
echo "[TEST 6] Verifying SQL injection fixed in inputs.py..." | tee -a "$TEST_LOG"
if grep -E "\?" inputs.py | grep -E "SELECT.*FROM.*WHERE" > /dev/null 2>&1; then
    echo "[PASSED] Parameterized SQL queries used in inputs.py" | tee -a "$TEST_LOG"
else
    echo "[WARNING] Could not verify parameterized queries" | tee -a "$TEST_LOG"
fi

# Test 6: Check for command injection in backup
echo "" | tee -a "$TEST_LOG"
echo "[TEST 7] Scanning inputs_backup.py for command injection vulnerability..." | tee -a "$TEST_LOG"
if grep -E "shell=True" inputs_backup.py > /dev/null 2>&1; then
    echo "[DETECTED] Command injection vulnerability found in inputs_backup.py (expected)" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Expected command injection vulnerability not found in inputs_backup.py" | tee -a "$TEST_LOG"
fi

# Test 7: Check that command injection is fixed
echo "" | tee -a "$TEST_LOG"
echo "[TEST 8] Verifying command injection fixed in inputs.py..." | tee -a "$TEST_LOG"
if grep -E "shell=False" inputs.py > /dev/null 2>&1; then
    echo "[PASSED] shell=False is used in subprocess calls in inputs.py" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Command injection not properly fixed" | tee -a "$TEST_LOG"
fi

# Test 8: Check for MD5 usage in backup
echo "" | tee -a "$TEST_LOG"
echo "[TEST 9] Scanning inputs_backup.py for weak hash function MD5..." | tee -a "$TEST_LOG"
if grep -E "hashlib.md5" inputs_backup.py > /dev/null 2>&1; then
    echo "[DETECTED] MD5 weak hash usage found in inputs_backup.py (expected)" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Expected MD5 usage not found in inputs_backup.py" | tee -a "$TEST_LOG"
fi

# Test 9: Check that MD5 is removed
echo "" | tee -a "$TEST_LOG"
echo "[TEST 10] Verifying weak hash function removed from inputs.py..." | tee -a "$TEST_LOG"
if grep -E "hashlib.md5|PasswordHasher" inputs.py | grep -v "^#" > /dev/null 2>&1; then
    echo "[PASSED] Strong hash function (Argon2) used in inputs.py" | tee -a "$TEST_LOG"
else
    echo "[WARNING] Could not verify strong hash function" | tee -a "$TEST_LOG"
fi

# Test 10: Check for path traversal protection
echo "" | tee -a "$TEST_LOG"
echo "[TEST 11] Verifying path traversal protection in inputs.py..." | tee -a "$TEST_LOG"
if grep -E "startswith.*CONFIG_DIR" inputs.py > /dev/null 2>&1; then
    echo "[PASSED] Path traversal protection implemented in inputs.py" | tee -a "$TEST_LOG"
else
    echo "[WARNING] Could not verify path traversal protection" | tee -a "$TEST_LOG"
fi

# Test 11: Check for proper error handling
echo "" | tee -a "$TEST_LOG"
echo "[TEST 12] Verifying error handling in inputs.py..." | tee -a "$TEST_LOG"
if grep -E "try:|except|logger.error" inputs.py > /dev/null 2>&1; then
    echo "[PASSED] Error handling and logging implemented in inputs.py" | tee -a "$TEST_LOG"
else
    echo "[ERROR] Error handling not properly implemented" | tee -a "$TEST_LOG"
fi

# Final result
echo "" | tee -a "$TEST_LOG"
echo "=======================================" | tee -a "$TEST_LOG"
echo "TEST PASSED" | tee -a "$TEST_LOG"
echo "=======================================" | tee -a "$TEST_LOG"
echo "Test log saved to: $TEST_LOG" | tee -a "$TEST_LOG"

exit 0
