#!/usr/bin/env python3
"""
Automated Test Execution Script
This script detects the current environment and runs the corresponding test script.
Results are logged with timestamps and status indicators.
"""

import os
import sys
import platform
import subprocess
import datetime
from pathlib import Path


def get_environment():
    """Detect the current environment (Windows/Linux/Docker)."""
    system = platform.system()
    
    # Check if running in Docker
    if os.path.exists('/.dockerenv') or os.path.exists('/run/.dockerenv'):
        return 'docker'
    elif system == 'Windows':
        return 'windows'
    elif system in ('Linux', 'Darwin'):  # Darwin is macOS
        return 'linux'
    else:
        return 'unknown'


def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_test_script_path(environment):
    """Get the path to the appropriate test script."""
    if environment == 'windows':
        return 'run_test.bat'
    elif environment in ('linux', 'docker'):
        return 'run_test.sh'
    else:
        return None


def append_to_log(log_file, message):
    """Append a message to the log file."""
    try:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    except IOError as e:
        print(f"ERROR: Could not write to log file: {e}", file=sys.stderr)


def run_test_on_file(test_script, log_file, file_to_test):
    """Run test script for a specific file."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Log test start
    append_to_log(log_file, f"\n{'='*50}")
    append_to_log(log_file, f"Testing: {file_to_test}")
    append_to_log(log_file, f"Timestamp: {timestamp}")
    append_to_log(log_file, '='*50)
    
    print(f"\n[{timestamp}] Running tests for {file_to_test}...")
    
    try:
        # Run the test script
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                ['cmd', '/c', test_script],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:  # Linux/macOS
            result = subprocess.run(
                ['bash', test_script],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        # Log output
        if result.stdout:
            append_to_log(log_file, "STDOUT:")
            append_to_log(log_file, result.stdout)
        
        if result.stderr:
            append_to_log(log_file, "STDERR:")
            append_to_log(log_file, result.stderr)
        
        # Determine test status
        test_status = "PASSED" if result.returncode == 0 else "FAILED"
        append_to_log(log_file, f"\nTest Result: {test_status}")
        append_to_log(log_file, f"Exit Code: {result.returncode}")
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        error_msg = "ERROR: Test script timed out after 60 seconds"
        append_to_log(log_file, error_msg)
        print(error_msg)
        return False
    
    except Exception as e:
        error_msg = f"ERROR: Failed to run test script: {e}"
        append_to_log(log_file, error_msg)
        print(error_msg)
        return False


def main():
    """Main function."""
    print("\n" + "="*50)
    print("Automated Security Audit Test Execution")
    print("="*50)
    
    # Detect environment
    environment = get_environment()
    print(f"\nDetected Environment: {environment}")
    
    # Create logs directory
    logs_dir = create_logs_directory()
    log_file = logs_dir / 'test_run.log'
    
    # Initialize log file with timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    append_to_log(str(log_file), f"\n{'='*60}")
    append_to_log(str(log_file), f"Test Execution Session: {timestamp}")
    append_to_log(str(log_file), f"Environment: {environment}")
    append_to_log(str(log_file), f"Platform: {platform.platform()}")
    append_to_log(str(log_file), '='*60)
    
    # Get test script
    test_script = get_test_script_path(environment)
    if not test_script:
        error_msg = f"ERROR: Unknown environment: {environment}"
        print(error_msg)
        append_to_log(str(log_file), error_msg)
        return 1
    
    if not os.path.exists(test_script):
        error_msg = f"ERROR: Test script not found: {test_script}"
        print(error_msg)
        append_to_log(str(log_file), error_msg)
        return 1
    
    print(f"Test Script: {test_script}")
    print(f"Log File: {log_file}")
    
    # Run tests for both files
    print("\n" + "="*50)
    print("Running Tests...")
    print("="*50)
    
    overall_status = True
    
    # Test inputs_backup.py (vulnerable version)
    print("\n[1/2] Testing inputs_backup.py (vulnerable version)...")
    backup_passed = run_test_on_file(test_script, str(log_file), 'inputs_backup.py')
    if not backup_passed:
        print("[ERROR] Backup file test failed")
        overall_status = False
    else:
        print("[SUCCESS] Backup file test passed")
    
    # Test inputs.py (secured version)
    print("\n[2/2] Testing inputs.py (secured version)...")
    secured_passed = run_test_on_file(test_script, str(log_file), 'inputs.py')
    if not secured_passed:
        print("[ERROR] Secured file test failed")
        overall_status = False
    else:
        print("[SUCCESS] Secured file test passed")
    
    # Final summary
    print("\n" + "="*50)
    print("Test Execution Summary")
    print("="*50)
    
    final_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_status = "TEST PASSED" if overall_status else "TEST FAILED"
    
    summary = f"""
Timestamp: {final_timestamp}
Environment: {environment}
inputs_backup.py: {'PASSED' if backup_passed else 'FAILED'}
inputs.py: {'PASSED' if secured_passed else 'FAILED'}
Overall Status: {final_status}
Log File: {log_file}
"""
    
    print(summary)
    append_to_log(str(log_file), summary)
    
    return 0 if overall_status else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
