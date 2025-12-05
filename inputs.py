import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify, abort
import subprocess
import yaml
import logging
from urllib.parse import urlparse

app = Flask(__name__)

# Load secrets from environment variables; provide safe defaults only for local dev
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH")

DB_FILE = os.getenv("DB_FILE", "appdata.db")

logging.basicConfig(level=logging.INFO)


def auth_user(info):
    username = info.get("username")
    if not username:
        abort(400, "username is required")
    if not INTERNAL_AUTH:
        abort(500, "server misconfiguration")
    raw = username + INTERNAL_AUTH
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return hashed


def query_profile(uid):
    if not uid:
        return []
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        q = "SELECT id,name,balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def is_valid_url(u):
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and p.netloc != ""
    except Exception:
        return False


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    if not target or amount is None or not url:
        abort(400, "missing parameters")
    if not is_valid_url(url):
        abort(400, "invalid notify_url")
    logging.info("transfer:%s:%s", target, amount)
    if not PAYMENT_TOKEN:
        abort(500, "server misconfiguration")
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error("notify failed: %s", e)
        return str(e)
    return resp.text


def update_records(path):
    # Only allow updating from an allowed directory to avoid arbitrary file read
    allowed_dir = os.getenv("CONFIG_DIR", ".")
    full_path = os.path.abspath(path)
    if not full_path.startswith(os.path.abspath(allowed_dir)):
        abort(403, "access denied")
    with open(full_path, "r", encoding="utf-8") as f:
        # safe_load already used; keep that for safety
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # sanitize name to avoid path traversal and shell injection
    if not name or any(c in name for c in ('/', '\\', '..')):
        abort(400, "invalid name")
    zip_path = f"{name}.zip"
    try:
        # use Python's zipfile instead of shelling out
        import zipfile
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    except Exception as e:
        logging.error("export failed: %s", e)
        abort(500, "export failed")
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    return jsonify({"token": auth_user(info)})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json or {}
    return jsonify({"result": transfer_funds(p)})


@app.route("/config", methods=["POST"])
def api_config():
    path = (request.json or {}).get("file")
    return jsonify(update_records(path))


@app.route("/export")
def api_export():
    name = request.args.get("name")
    export_data(name)
    return jsonify({"ok": 1})


if __name__ == "__main__":
    # Never run production with debug=True
    app.run(debug=False, host="0.0.0.0")
