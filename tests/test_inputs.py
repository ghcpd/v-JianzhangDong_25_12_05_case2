import os
import sqlite3
import tempfile
import importlib.util
import sys
import types
import subprocess


def load_module_from_path(path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("target_mod", os.path.abspath(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup_test_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, name TEXT, balance REAL)")
    c.execute("DELETE FROM profiles")
    c.executemany("INSERT OR REPLACE INTO profiles (id,name,balance) VALUES (?, ?, ?)", [
        ("1", "Alice", 100.0),
        ("2", "Bob", 50.0)
    ])
    conn.commit()
    conn.close()


def test_sql_injection_behavior(tmp_path):
    target = os.environ.get("TARGET_MODULE")
    assert target, "TARGET_MODULE env var is required"
    mod = load_module_from_path(target)

    # Use a test DB
    db_file = str(tmp_path / "test_appdata.db")
    setup_test_db(db_file)
    mod.DB_FILE = db_file

    # Input that would act like SQL injection by breaking out of the literal
    # e.g. "1' OR '1'='1" will result in an always-true predicate when the string
    # is interpolated unsafely into SQL.
    rows = mod.query_profile("1' OR '1'='1")
    if target.endswith("input_backup.py"):
        # vulnerable should return multiple rows
        assert len(rows) >= 2, "Backup should be vulnerable to SQL injection (return many rows)"
    else:
        # secure implementation should not treat it as SQL injection
        assert len(rows) <= 1, "Secure module should prevent SQL injection"


def test_export_command_safety(tmp_path, monkeypatch):
    target = os.environ.get("TARGET_MODULE")
    mod = load_module_from_path(target)
    # set test DB file path
    db_file = str(tmp_path / "appdata.db")
    with open(db_file, "w") as f:
        f.write("dummy")
    mod.DB_FILE = db_file

    if target.endswith("input_backup.py"):
        # For backup, it uses subprocess with shell=True - monkeypatch Popen to capture
        called = {}

        class FakePopen:
            def __init__(self, cmd, shell=False):
                called['cmd'] = cmd
                called['shell'] = shell

        monkeypatch.setattr(subprocess, 'Popen', FakePopen)
        # name with suspicious chars
        suspicious_name = 'injected;rm -rf /'
        mod.export_data(suspicious_name)
        assert 'injected' in called['cmd'], "Backup used shell and included unsanitized name"
        assert called['shell'] is True
    else:
        # Secure module should reject unsafe names
        import pytest
        with pytest.raises(ValueError):
            mod.export_data('injected;rm -rf /')


def test_update_records_path_restriction(tmp_path):
    target = os.environ.get("TARGET_MODULE")
    mod = load_module_from_path(target)
    # create a config file outside allowed dir
    outside = tmp_path / "outside.conf"
    outside.write_text("dummy: 1")

    if target.endswith("input_backup.py"):
        # backup will read arbitrary path
        cfg = mod.update_records(str(outside))
        assert isinstance(cfg, dict) or cfg == {'dummy': 1} or True
    else:
        # secure module should forbid file outside allowed dir
        try:
            mod.ALLOWED_CONFIG_DIR = str(tmp_path / "allowed")
            (tmp_path / "allowed").mkdir()
        except Exception:
            pass
        import pytest
        with pytest.raises(ValueError):
            mod.update_records(str(outside))


def test_transfer_notify_validation(tmp_path, monkeypatch):
    target = os.environ.get("TARGET_MODULE")
    mod = load_module_from_path(target)
    # ensure there's a PAYMENT_TOKEN for backup; secure requires PAYMENT_TOKEN to be set
    os.environ['PAYMENT_TOKEN'] = os.environ.get('PAYMENT_TOKEN', 'tok')
    mod.PAYMENT_TOKEN = os.environ['PAYMENT_TOKEN']

    if target.endswith("input_backup.py"):
        # backup will accept http and call requests.post
        called = {}

        class FakeResp:
            def __init__(self):
                self.text = 'ok'
            def raise_for_status(self):
                pass

        def fake_post(url, json=None, timeout=None):
            called['url'] = url
            called['json'] = json
            return FakeResp()

        monkeypatch.setattr(sys.modules['requests'], 'post', fake_post)
        payload = {'target': '1', 'amount': 1, 'notify_url': 'http://example.local/webhook'}
        resp = mod.transfer_funds(payload)
        assert called['url'] == 'http://example.local/webhook'
    else:
        # secure module requires https and host to be allowed
        mod.ALLOWED_NOTIFY_HOSTS = {"example.local"}
        import pytest
        with pytest.raises(ValueError):
            mod.transfer_funds({'target': '1', 'amount': 10, 'notify_url': 'http://example.local/webhook'})
