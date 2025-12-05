import os
import platform
import subprocess
import datetime

LOG_DIR = os.path.join('logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')

FILES_TO_TEST = ['input_backup.py', 'inputs.py']

def ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'

def run_single_file(file_path):
    cmd = ["python", "security_test_runner.py", file_path]
    with open(LOG_FILE, 'a', encoding='utf-8') as lf:
        lf.write(f"[{ts()}] RUN: {cmd}\n")
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = p.stdout.decode('utf-8', errors='replace')
            lf.write(out + '\n')
            status = 'TEST PASSED' if p.returncode == 0 else 'TEST FAILED'
            lf.write(f"[{ts()}] {status} (file={file_path}, exit={p.returncode})\n\n")
            return p.returncode == 0
        except Exception as e:
            lf.write(str(e) + '\n')
            lf.write(f"[{ts()}] TEST FAILED (exception) (file={file_path})\n\n")
            return False


def detect_environment():
    # Simple detection for Docker: check for /.dockerenv or cgroup
    if os.path.exists('/.dockerenv'):
        return 'Docker'
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                return 'Docker'
    except Exception:
        pass
    return platform.system()


if __name__ == '__main__':
    env = detect_environment()
    with open(LOG_FILE, 'a', encoding='utf-8') as lf:
        lf.write(f"[{ts()}] DETECTED_ENV: {env}\n")

    results = []
    for f in FILES_TO_TEST:
        ok = run_single_file(f)
        results.append({'file': f, 'ok': ok})

    overall = all(r['ok'] for r in results)
    with open(LOG_FILE, 'a', encoding='utf-8') as lf:
        lf.write(f"[{ts()}] OVERALL: {'TEST PASSED' if overall else 'TEST FAILED'}\n")
    if not overall:
        raise SystemExit(1)