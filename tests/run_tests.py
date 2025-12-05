import sys
import re

VULN_PATTERNS = [
    ("hardcoded_secret", re.compile(r"PAYMENT_TOKEN\s*=\s*\".*\"|MAIL_SERVER_KEY\s*=\s*\".*\"|INTERNAL_AUTH\s*=\s*\".*\"")),
    ("md5_hash", re.compile(r"hashlib\.md5\(")),
    ("sql_injection", re.compile(r"WHERE id\s*=\s*'%s'|execute\([^)]*%")),
    ("subprocess_shell", re.compile(r"subprocess\.Popen\([^)]*shell=True|\bzip\s+\{\w+\}\.zip")),
    # requests.post without timeout - handled programmatically below
    ("debug_mode", re.compile(r"app\.run\(.*debug=True.*\)")),
    ("open_yaml_arbitrary", re.compile(r"with open\(path\) as f:.*yaml\.safe_load", re.S)),
]


def check_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    findings = []
    for name, pattern in VULN_PATTERNS:
        if name == 'requests_no_timeout':
            continue
        if pattern.search(content):
            findings.append(name)

    # Programmatically detect requests.post occurrences and verify 'timeout=' is present in each call
    idx = 0
    while True:
        idx = content.find('requests.post(', idx)
        if idx == -1:
            break
        start = idx + len('requests.post(')
        # find matching closing paren (simple counter)
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
            i += 1
        call_text = content[start:i-1]
        if 'timeout=' not in call_text:
            findings.append('requests_no_timeout')
            break
        idx = i
    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage: run_tests.py <file>")
        sys.exit(2)
    path = sys.argv[1]
    findings = check_file(path)
    if findings:
        print(f"VULNERABILITIES FOUND in {path}:")
        for f in findings:
            print(f" - {f}")
        sys.exit(1)
    print(f"No high-level issues found in {path}.")
    sys.exit(0)


if __name__ == '__main__':
    main()
