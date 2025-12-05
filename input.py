import os
import sqlite3
import hashlib
import hmac
import logging
import requests
from flask import Flask, request, jsonify
import yaml
import zipfile
import re
from urllib.parse import urlparse

app = Flask(__name__)

# Load secrets and configuration from environment - do not hardcode secrets
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")

# File locations can be configured via environment variables for safety in tests
DB_FILE = os.environ.get("DB_FILE", "appdata.db")
ALLOWED_CONFIG_DIR = os.environ.get("ALLOWED_CONFIG_DIR", os.path.abspath("./configs"))
ALLOWED_NOTIFY_HOSTS = set(h.strip().lower() for h in os.environ.get("ALLOWED_NOTIFY_HOSTS", "localhost,127.0.0.1").split(",") if h)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _safe_filename(name: str) -> bool:
    # Allow only simple safe file name characters
    if not isinstance(name, str):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", name))


def auth_user(info: dict) -> str:
    """Create a secure HMAC token for a username using INTERNAL_AUTH from env.

    Returns an HMAC-SHA256 digest. Raises ValueError if configuration is missing or input invalid.
    """
    if not INTERNAL_AUTH:
        raise RuntimeError("Server not configured: INTERNAL_AUTH unset")
    username = info.get("username", "")
    if not isinstance(username, str) or not username:
        raise ValueError("username required")
    digest = hmac.new(INTERNAL_AUTH.encode("utf-8"), username.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def query_profile(uid: str):
    """Query a profile using a parameterized SQL query to prevent injection.

    uid is treated as a string identifier; SQL parameters are used.
    """
    if not isinstance(uid, str):
        raise ValueError("uid must be a string")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        q = "SELECT id,name,balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
        return data
    finally:
        conn.close()


def transfer_funds(payload: dict):
    """Safely notify a payment gateway of a transfer while validating inputs.

    The notify_url must be HTTPS and host must be in ALLOWED_NOTIFY_HOSTS; token is loaded
    from environment (PAYMENT_TOKEN). Exceptions are caught and raised as RuntimeError.
    """
    if PAYMENT_TOKEN is None:
        raise RuntimeError("Server not configured: PAYMENT_TOKEN unset")
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")

    # Basic validation
    if not target or not isinstance(target, str):
        raise ValueError("missing target")
    try:
        amount_f = float(amount)
    except Exception:
        raise ValueError("amount must be numeric")
    if amount_f <= 0:
        raise ValueError("amount must be positive")

    # Validate URL and host allowlist
    parsed = urlparse(url if isinstance(url, str) else "")
    if parsed.scheme not in ("https",):
        raise ValueError("notify_url must be https")
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    if hostname not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("notify_url host not allowed")

    logger.info("transfer: %s -> %s", target, amount_f)
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount_f}, timeout=5)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error("error notifying payment gateway: %s", e)
        raise RuntimeError("failed to notify payment gateway")


def update_records(path: str):
    """Safely load a YAML configuration file restricted to ALLOWED_CONFIG_DIR.

    Prevents path traversal and arbitrary file read. Returns a decoded config dict.
    """
    if not isinstance(path, str) or not path:
        raise ValueError("file path required")
    # build absolute path and ensure it is inside allowed directory
    cfg_path = os.path.abspath(path)
    if not cfg_path.startswith(os.path.abspath(ALLOWED_CONFIG_DIR) + os.sep):
        raise ValueError("access to the requested file is forbidden")
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError("config file not found")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name: str):
    """Safely export the DB_FILE into a zip using Python zipfile (no shell/command injection).

    name must be a safe filename (alphanumeric, underscore, hyphen).
    """
    if not _safe_filename(name):
        raise ValueError("invalid export name")
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError("database file not found")
    out_name = f"{name}.zip"
    # create zip archive safely
    with zipfile.ZipFile(out_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        return jsonify(query_profile(uid))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/config", methods=["POST"])
def api_config():
    path = request.json.get("file") if request.json else None
    try:
        return jsonify(update_records(path))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/export")
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
        return jsonify({"ok": 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # Only enable debug when explicitly requested via environment variable
    debug = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")
    app.run(debug=debug)
