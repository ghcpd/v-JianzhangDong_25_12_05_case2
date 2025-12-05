import sys
import importlib.util
import os

def import_file(path):
    if not os.path.exists(path):
        print(f"file not found: {path}")
        return 2
    try:
        spec = importlib.util.spec_from_file_location('mod', path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        print(f"{path} import OK")
        return 0
    except Exception as e:
        print(f"{path} import failed: {e}")
        return 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python single_import_test.py <file>')
        sys.exit(2)
    path = sys.argv[1]
    rc = import_file(path)
    sys.exit(rc)
