import os
import platform
import subprocess
from datetime import datetime

LOG_DIR = os.path.join("logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")


def timestamp():
    return datetime.utcnow().isoformat() + "Z"


def detect_env():
    # Detect Docker by checking /.dockerenv or cgroup
    if os.path.exists("/.dockerenv"):
        return "docker"
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                return 'docker'
    except Exception:
        pass
    system = platform.system().lower()
    if system.startswith('linux') or system.startswith('darwin'):
        return 'linux'
    if system.startswith('windows'):
        return 'windows'
    return 'unknown'


def run_command_for_target(env_type, target_module):
    # Use provided run scripts
    if env_type in ('linux', 'docker'):
        cmd = ["bash", "run_test.sh", target_module]
    elif env_type == 'windows':
        cmd = ["cmd.exe", "/c", "run_test.bat", target_module]
    else:
        raise RuntimeError("Unsupported environment")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def main():
    env = detect_env()
    header = f"[{timestamp()}] auto_test starting, environment={env}\n"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(header)
    overall_success = True

    for module in ["input_backup.py", "input.py"]:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp()}] Running tests for {module}\n")
        code, out = run_command_for_target(env, module)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(out)
            status_line = f"[{timestamp()}] {module} EXIT {code}\n"
            f.write(status_line)
            if code == 0:
                f.write(f"[{timestamp()}] {module} TEST PASSED\n")
            else:
                f.write(f"[{timestamp()}] {module} TEST FAILED\n")
        if code != 0:
            overall_success = False

    final = "TEST PASSED" if overall_success else "TEST FAILED"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp()}] FINAL: {final}\n")

    print(final)
    return 0 if overall_success else 2


if __name__ == '__main__':
    raise SystemExit(main())
