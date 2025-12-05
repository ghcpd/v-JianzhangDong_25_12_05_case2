import os
import sqlite3
import requests
import hashlib
import hmac
import logging
import re
import zipfile
from io import BytesIO
from functools import wraps
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort
import yaml

app = Flask(__name__)

# Configuration from environment variables (no hardcoded secrets)
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "./config")

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper: ensure required secrets are set
required = ["INTERNAL_AUTH", "ADMIN_API_KEY"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    logger.warning("Missing required environment variables: %s", missing)

# Utility functions
def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if not key or key != ADMIN_API_KEY:
            abort(401, description="Unauthorized")
        return func(*args, **kwargs)
    return wrapper


def auth_user(info):
    username = info.get("username", "")
    if not isinstance(username, str) or len(username) > 64:
        raise ValueError("Invalid username")
    # Use HMAC-SHA256 with a secret key instead of MD5
    if not INTERNAL_AUTH:
        raise RuntimeError("Server misconfigured: INTERNAL_AUTH not set")
    token = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256).hexdigest()
    return token


def query_profile(uid):
    # Validate uid is numeric
    if not uid or not re.fullmatch(r"\d+", str(uid)):
        raise ValueError("Invalid user id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        q = "SELECT id, name, balance FROM profiles WHERE id = ?"
        c.execute(q, (int(uid),))
        data = c.fetchall()
        return data
    finally:
        conn.close()


def is_safe_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https",):
            return False
        host = parsed.hostname
        if not host:
            return False
        # Block localhost and private IPs (basic checks)
        blocked = ("localhost", "127.0.0.1", "::1")
        if host in blocked:
            return False
        return True
    except Exception:
        return False


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")

    # Basic validation
    if not target or not isinstance(target, str):
        raise ValueError("Invalid target")
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            raise ValueError("Amount must be positive")
    except Exception:
        raise ValueError("Invalid amount")

    if not is_safe_url(url):
        raise ValueError("Invalid notify_url")

    logger.info("Initiating transfer to target=%s amount=sanitized", "REDACTED")
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount_val}, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        logger.exception("Failed to notify payment endpoint: %s", e)
        raise
    return resp.text


def update_records(path):
    # Only allow config files from CONFIG_DIR and restrict file extensions
    if not path or not isinstance(path, str):
        raise ValueError("Invalid file path")
    abs_dir = os.path.realpath(CONFIG_DIR)
    abs_path = os.path.realpath(os.path.join(abs_dir, path))
    if not abs_path.startswith(abs_dir):
        raise ValueError("Access denied")
    if not abs_path.endswith(('.yaml', '.yml')):
        raise ValueError("Unsupported file type")
    with open(abs_path, 'r') as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize name and use Python's zipfile module (no shell)
    if not name or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Invalid archive name")
    archive_path = f"{name}.zip"
    try:
        with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
        return True
    except Exception:
        logger.exception("Failed to export data")
        return False


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"token": token})


@app.route("/profile")
@require_api_key
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(data)


@app.route("/transfer", methods=["POST"])
@require_api_key
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
@require_api_key
def api_config():
    path = (request.json or {}).get("file")
    try:
        cfg = update_records(path)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(cfg)


@app.route("/export")
@require_api_key
def api_export():
    name = request.args.get("name")
    try:
        ok = export_data(name)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": 1 if ok else 0})


if __name__ == "__main__":
    debug_flag = os.environ.get('FLASK_DEBUG') == '1'
    app.run(host='0.0.0.0', debug=debug_flag)
