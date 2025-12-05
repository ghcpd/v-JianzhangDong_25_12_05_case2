# Security Audit and Test Kit

Overview
- `input_backup.py`: original file (insecure) preserved as backup
- `inputs.py`: secured code with fixes applied
- `report.json`: structured vulnerability report and remediation details
- `tests/run_tests.py`: static pattern-based tests to detect insecure patterns
- `run_test.sh` / `run_test.bat`: platform-specific test runners
- `auto_test.py`: automatic test executor that runs both backup and fixed tests and logs results
- `requirements.txt`, `Dockerfile`, `setup.sh`: environment and setup helpers

Setup
1. Create a virtual environment and install dependencies:
   - Linux/macOS: ./setup.sh
   - Windows: python -m pip install -r requirements.txt

Running tests
- Linux/macOS: ./run_test.sh <file>
- Windows: run_test.bat <file>
- If no <file> is provided, defaults to `inputs.py`.

Automated tests
- Use `auto_test.py` to run tests for both `input_backup.py` and `inputs.py`. Logs are saved to `logs/test_run.log`.

Docker
- Build: docker build -t audit .
- Run (example): docker run --rm audit

Interpreting logs
- `logs/test_run.log` contains timestamps, command outputs, and final `TEST PASSED` or `TEST FAILED` line.
