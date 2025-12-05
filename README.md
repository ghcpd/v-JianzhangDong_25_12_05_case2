# Security audit and tests for inputs.py

This repository includes an audited and hardening-fixed version of the original `inputs.py`, a backup of the original, automated tests that demonstrate the issues in the original and verify the fixes, and environment/run scripts.

Files Overview
- `inputs.py` — original file as provided in the workspace (unchanged)
- `input_backup.py` — **backup copy of the original** (created before any fixes)
- `input.py` — **repaired / secure version** of the application
- `tests/test_inputs.py` — pytest-based unit tests which dynamically load a target module (specified via environment variable `TARGET_MODULE`) and check for vulnerabilities or mitigations.
- `run_test.sh` / `run_test.bat` — helper scripts to run the tests for a particular target module, usage: `run_test.sh input_backup.py` or `run_test.sh input.py`
- `auto_test.py` — automatic test executor which detects platform (Linux/Windows/Docker) and runs tests for both `input_backup.py` and `input.py` in sequence, saving logs to `logs/test_run.log` with timestamps and final status.
- `report.json` — structured vulnerability report outlining each issue found and the applied fixes.
- `requirements.txt`, `Dockerfile`, `setup.sh` — environment files for easy replication.

Quick setup

Linux / macOS

1. Create and activate a virtualenv and install deps (or use `setup.sh`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run tests manually for the original backup:

```bash
./run_test.sh input_backup.py
```

3. Run tests for the fixed version:

```bash
./run_test.sh input.py
```

Windows

1. Install dependencies, e.g., in an activated venv:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Run tests:

```powershell
.\run_test.bat input_backup.py
.\run_test.bat input.py
```

Auto testing and logs

- Use the automatic test runner:

```bash
python auto_test.py
```

- `auto_test.py` runs tests for both `input_backup.py` and `input.py` and appends output to `logs/test_run.log`. Each test run is annotated with a timestamp and an exit status line. The final status will be either `TEST PASSED` or `TEST FAILED`.

Notes & Security recommendations
- Never hardcode secrets in source files — use environment variables or a secrets manager.
- Use parameterized queries for SQL access to prevent SQL injection.
- Avoid using shell=True with untrusted data; prefer high-level libraries (e.g., zipfile) for file operations.
- Restrict server-side requests to a well-defined allowlist and require HTTPS.
- Turn off debug mode in production deployments.

If anything should be adjusted (e.g., different allowed hosts, config path), update environment variables described in `input.py`.
