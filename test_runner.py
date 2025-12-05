import sys
import re

VULN_PATTERNS = [
    r'PAYMENT_TOKEN\s*=\s*["\']',
    r'MAIL_SERVER_KEY\s*=\s*["\']',
    r'INTERNAL_AUTH\s*=\s*["\']',
    r"hashlib\.md5",
    r"WHERE id = '%s'",
    r"%\s*uid",
    r"subprocess\.Popen\(",
    r"shell=True",
    r"app\.run\(debug=True\)",
    r"request\.json\.get\(\s*[\'\"]file[\'\"]",
]

SECURE_INDICATORS = [
    r"hmac\.new",
    r"require_api_key",
    r"zipfile\.ZipFile",
    r"c\.execute\(q,\s*\(",
    r"INTERNAL_AUTH\s*=\s*os\.environ",
]


def run_checks(path, expected):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    vuln_found = {p: bool(re.search(p, content)) for p in VULN_PATTERNS}
    secure_found = {p: bool(re.search(p, content)) for p in SECURE_INDICATORS}

    if expected == 'vulnerable':
        # Expect at least one vuln pattern to be present
        vuln_present = any(vuln_found.values())
        secure_absent = not any(secure_found.values())
        if vuln_present and secure_absent:
            print(f"[OK] {path} is vulnerable as expected. Found vulnerability signatures:")
            for p, v in vuln_found.items():
                if v:
                    print(f" - {p}")
            return 0
        else:
            print(f"[FAIL] Expected vulnerabilities in {path}, but checks failed.")
            print("Vuln patterns found:")
            for p, v in vuln_found.items():
                print(f"{p}: {v}")
            print("Secure indicators found (should be absent):")
            for p, v in secure_found.items():
                print(f"{p}: {v}")
            return 2
    elif expected == 'secure':
        # Expect no vuln patterns and presence of secure indicators
        vuln_absent = not any(vuln_found.values())
        secure_present = any(secure_found.values())
        if vuln_absent and secure_present:
            print(f"[OK] {path} appears secure. Secure indicators present:")
            for p, v in secure_found.items():
                if v:
                    print(f" - {p}")
            return 0
        else:
            print(f"[FAIL] Expected secure code in {path}, but checks failed.")
            print("Vuln patterns found (should be absent):")
            for p, v in vuln_found.items():
                print(f"{p}: {v}")
            print("Secure indicators found:")
            for p, v in secure_found.items():
                print(f"{p}: {v}")
            return 3
    else:
        print("Unknown expected value. Use 'vulnerable' or 'secure'.")
        return 4


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python test_runner.py <file> <vulnerable|secure>")
        sys.exit(1)
    path = sys.argv[1]
    expected = sys.argv[2]
    rc = run_checks(path, expected)
    sys.exit(rc)
