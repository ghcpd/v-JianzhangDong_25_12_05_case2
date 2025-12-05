import os
import sys
import subprocess
import platform
import datetime

LOG_DIR = os.path.join('logs')
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')

os.makedirs(LOG_DIR, exist_ok=True)

def timestamp():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def run_cmd(cmd, shell=False):
    proc = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode('utf-8', errors='replace')


def run_tests_for_file(file, expected):
    system = platform.system()
    if system == 'Windows':
        cmd = ['run_test.bat', file, expected]
        shell = False
    else:
        cmd = ['./run_test.sh', file, expected]
        shell = False
    rc, out = run_cmd(cmd, shell=shell)
    return rc, out


def main():
    entries = [
        ("input_backup.py", 'vulnerable'),
        ("inputs.py", 'secure'),
    ]
    overall_success = True
    with open(LOG_FILE, 'a', encoding='utf-8') as fh:
        fh.write(f"{timestamp()} - Starting auto_test run\n")
        for fname, expected in entries:
            fh.write(f"{timestamp()} - Running tests for {fname} (expect: {expected})\n")
            rc, out = run_tests_for_file(fname, expected)
            fh.write(f"{timestamp()} - Output:\n")
            fh.write(out + '\n')
            status = 'TEST PASSED' if rc == 0 else 'TEST FAILED'
            fh.write(f"{timestamp()} - {fname} - exit_code={rc} - {status}\n")
            if rc != 0:
                overall_success = False
        final = 'TEST PASSED' if overall_success else 'TEST FAILED'
        fh.write(f"{timestamp()} - Final result: {final}\n")
    print(final)
    sys.exit(0 if overall_success else 2)

if __name__ == '__main__':
    main()
