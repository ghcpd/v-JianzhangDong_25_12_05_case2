import os
import subprocess
import sys
from datetime import datetime

LOG_DIR = os.path.join("logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")


def run_cmd(cmd):
    t = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"[{t}] RUN: {cmd}\n")
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    exit_code = proc.returncode
    t2 = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"[{t2}] EXIT {exit_code}\n")
        fh.write(out.decode(errors='replace'))
        fh.write("\n")
    return exit_code, out.decode(errors='replace')


def main():
    is_windows = os.name == 'nt'
    if is_windows:
        runner = "run_test.bat"
    else:
        runner = "./run_test.sh"

    tests = [
        ("input_backup.py", f"{runner} input_backup.py"),
        ("inputs.py", f"{runner} inputs.py"),
    ]

    results = []
    for name, cmd in tests:
        code, out = run_cmd(cmd)
        results.append({"file": name, "exit": code, "output": out})

    # Criteria: backup should be vulnerable (exit != 0) and inputs.py should be clean (exit == 0)
    backup_pass = results[0]["exit"] != 0
    fixed_pass = results[1]["exit"] == 0
    final_status = backup_pass and fixed_pass

    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"FINAL STATUS: {'TEST PASSED' if final_status else 'TEST FAILED'}\n")

    print("TEST PASSED" if final_status else "TEST FAILED")
    sys.exit(0 if final_status else 2)


if __name__ == '__main__':
    main()
