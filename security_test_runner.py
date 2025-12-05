import sys
import os
import re
import importlib.util
import hashlib
import tempfile
import zipfile

def static_checks(path):
    failures = []
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    if re.search(r"\bPAYMENT_TOKEN\b\s*=\s*['\"]", text):
        failures.append('Hardcoded PAYMENT_TOKEN')
    if re.search(r"\bMAIL_SERVER_KEY\b\s*=\s*['\"]", text):
        failures.append('Hardcoded MAIL_SERVER_KEY')
    if re.search(r"\bINTERNAL_AUTH\b\s*=\s*['\"]", text):
        failures.append('Hardcoded INTERNAL_AUTH')
    if 'hashlib.md5(' in text:
        failures.append('Use of MD5')
    if re.search(r"WHERE .*id .*%", text):
        failures.append('Possible SQL string formatting')
    if 'subprocess.Popen' in text and 'shell=True' in text:
        failures.append('Use of subprocess with shell=True')
    if re.search(r"app\.run\(.*debug\s*=\s*True", text):
        failures.append('Flask debug mode enabled')
    return failures

def import_module_from_path(path):
    name = 'mod_' + hashlib.sha1(os.path.abspath(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def dynamic_checks(module, path):
    failures = []
    # Ensure requests usage includes timeout by monkeypatching requests in module
    try:
        class DummyResp:
            def __init__(self):
                self.text = 'ok'
            def raise_for_status(self):
                return None

        class DummyRequests:
            def __init__(self):
                self.last = None
            def post(self, url, json=None, **kwargs):
                self.last = {'url': url, 'json': json, 'kwargs': kwargs}
                return DummyResp()

        # inject dummy requests
        module.requests = DummyRequests()
        if hasattr(module, 'transfer_funds'):
            try:
                rc = module.transfer_funds({'target': 't', 'amount': 1, 'notify_url': 'http://example.com/notify'})
                last = module.requests.last
                if not last:
                    failures.append('transfer_funds did not call requests.post')
                else:
                    # check timeout presence
                    if 'timeout' not in last['kwargs']:
                        failures.append('requests.post called without timeout')
            except Exception as e:
                failures.append(f'transfer_funds raised exception: {e}')
        # Test export_data: create temporary DB file and verify zip created (if function uses zipfile)
        if hasattr(module, 'export_data'):
            tmpdb = tempfile.NamedTemporaryFile(delete=False)
            try:
                tmpdb.write(b'db')
                tmpdb.close()
                module.DB_FILE = tmpdb.name
                try:
                    ok = module.export_data('pytest_export')
                    zname = 'pytest_export.zip'
                    if not os.path.exists(zname):
                        failures.append('export_data did not create zip')
                    else:
                        try:
                            with zipfile.ZipFile(zname, 'r') as zf:
                                names = zf.namelist()
                                if os.path.basename(module.DB_FILE) not in names:
                                    failures.append('DB file not found inside zip')
                        except Exception as e:
                            failures.append(f'zip verification failed: {e}')
                        finally:
                            try:
                                os.remove(zname)
                            except Exception:
                                pass
                except Exception as e:
                    failures.append(f'export_data raised exception: {e}')
            finally:
                try:
                    os.remove(tmpdb.name)
                except Exception:
                    pass
    except Exception as e:
        failures.append(f'dynamic check error: {e}')
    return failures

def main():
    if len(sys.argv) < 2:
        print('usage: python security_test_runner.py <path_to_file>')
        return 2
    path = sys.argv[1]
    if not os.path.exists(path):
        print('file not found:', path)
        return 2
    print('Running static checks on', path)
    s = static_checks(path)
    if s:
        print('Static check failures:')
        for it in s:
            print('-', it)
        return 1
    print('Static checks passed; importing module for dynamic checks')
    # set safe environment values
    os.environ.setdefault('PAYMENT_TOKEN', 'test-token')
    os.environ.setdefault('INTERNAL_AUTH', 'test-internal')
    os.environ.setdefault('CONFIG_DIR', os.getcwd())
    try:
        module = import_module_from_path(path)
    except Exception as e:
        print('Import failed:', e)
        return 1
    d = dynamic_checks(module, path)
    if d:
        print('Dynamic check failures:')
        for it in d:
            print('-', it)
        return 1
    print('All security checks passed for', path)
    return 0

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
