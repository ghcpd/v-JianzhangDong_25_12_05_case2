import importlib.util
import sys

files = ['input_backup.py', 'inputs.py']
results = {}
for f in files:
    try:
        spec = importlib.util.spec_from_file_location('mod', f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        print(f"{f} imported OK")
        results[f] = 0
    except Exception as e:
        print(f"{f} import failed: {e}")
        results[f] = 1

sys.exit(1 if any(results.values()) else 0)
