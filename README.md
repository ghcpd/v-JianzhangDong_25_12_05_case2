# Project Security Audit and Test Runner

Overview
- `inputs.py`: Secured application source.
- `input_backup.py`: Backup of the original, vulnerable source.
- `report.json`: Structured vulnerability report and fixes.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: Container image for running the app.
- `setup.sh`: Environment setup script for Linux/macOS.
- `run_test.sh`: POSIX test runner that imports both files.
- `run_test.bat`: Windows test runner.
- `auto_test.py`: Detects OS and runs the appropriate test script, logs to `logs/test_run.log`.
- `logs/`: Directory where test logs are stored.

Setup
1. Linux/macOS (recommended):
   - Ensure Python 3.8+ installed.
   - Run:
```bash
chmod +x setup.sh run_test.sh
./setup.sh
```

2. Windows:
   - Ensure Python 3.8+ is on PATH.
   - (Optional) Create a venv: `python -m venv .venv` and activate it.
   - Install requirements: `pip install -r requirements.txt`

Running Tests
- Linux/macOS: `./run_test.sh`
- Windows: `run_test.bat`
- Docker: `docker build -t secure-app . && docker run --rm -p 5000:5000 secure-app`

Auto Test
- Run `python auto_test.py` to detect environment and run tests automatically.
- Logs are appended to `logs/test_run.log` with timestamps and final status lines `TEST PASSED` or `TEST FAILED`.

Interpreting Logs
- Each test invocation writes the command, its output, and a status line.
- The final `OVERALL` line indicates whether all tests passed.
