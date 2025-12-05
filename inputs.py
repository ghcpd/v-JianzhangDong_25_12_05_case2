import os
import sqlite3
import requests
import hashlib
import hmac
import logging
import re
import zipfile
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort
import yaml

app = Flask(__name__)

# Load secrets from environment variables; fail if missing
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")

if not PAYMENT_TOKEN or not MAIL_SERVER_KEY or not INTERNAL_AUTH:
    raise RuntimeError("Missing required environment variables for secrets")

DB_FILE = os.environ.get("DB_FILE", "appdata.db")

# Allowed notify hosts (comma-separated) - set via env var to restrict SSRF
ALLOWED_NOTIFY_HOSTS = set(h.strip() for h in os.environ.get("ALLOWED_NOTIFY_HOSTS", "").split(",") if h.strip())


def auth_user(info: dict) -> str:
    """Generate HMAC-SHA256 token for the user with server-side secret."""
    username = info.get("username", "")
    if not username:
        raise ValueError("username is required")
    digest = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256).hexdigest()
    return digest


def query_profile(uid):
    # Validate uid: only allow integers
    if not re.fullmatch(r"\d+", str(uid)):
        raise ValueError("invalid user id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, balance FROM profiles WHERE id = ?", (int(uid),))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    logging.info("transfer requested for target=%s amount=%s", target, amount)
    # Validate notify URL to prevent SSRF: must be https and in allowed hosts if configured
    parsed = urlparse(url or "")
    if parsed.scheme not in ("https",):
        raise ValueError("notify_url must use https")
    host = parsed.hostname or ""
    if ALLOWED_NOTIFY_HOSTS and host not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("notify_url host not allowed")
    # Make outbound request with timeout and do not send secrets in logs
    resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
    resp.raise_for_status()
    return resp.text


def update_records(path):
    # Only allow configs within a secure config directory
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "configs"))
    target = os.path.abspath(os.path.join(base, path))
    if not target.startswith(base + os.sep):
        raise ValueError("invalid config path")
    with open(target) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize the provided name to alphanumerics and underscores only
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name or ""):
        raise ValueError("invalid export name")
    archive_name = f"{name}.zip"
    # Use Python's zipfile to avoid shell injection
    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zf:
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
        return jsonify({"result": transfer_funds(p)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/config", methods=["POST"])
def api_config():
    path = (request.json or {}).get("file")
    try:
        return jsonify(update_records(path))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/export")
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": 1})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
