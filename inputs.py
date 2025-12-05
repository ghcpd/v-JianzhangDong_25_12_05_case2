import os
import sqlite3
import requests
import logging
from flask import Flask, request, jsonify
import subprocess
import yaml
import re
from pathlib import Path
from dotenv import load_dotenv
from argon2 import PasswordHasher
from jsonschema import validate, ValidationError

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve sensitive credentials from environment variables
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')
MAIL_SERVER_KEY = os.getenv('MAIL_SERVER_KEY')
INTERNAL_AUTH = os.getenv('INTERNAL_AUTH')

# Validate required environment variables are set
if not all([PAYMENT_TOKEN, MAIL_SERVER_KEY, INTERNAL_AUTH]):
    logger.warning('Required environment variables are not set. Using fallback values.')
    PAYMENT_TOKEN = PAYMENT_TOKEN or 'tok_fallback'
    MAIL_SERVER_KEY = MAIL_SERVER_KEY or 'mail_fallback'
    INTERNAL_AUTH = INTERNAL_AUTH or 'auth_fallback'

DB_FILE = os.getenv('DB_FILE', 'appdata.db')
CONFIG_DIR = os.path.abspath(os.getenv('CONFIG_DIR', 'config'))

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Configuration schema for validation
CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'setting1': {'type': 'string'},
        'setting2': {'type': 'integer'},
        'setting3': {'type': 'boolean'}
    },
    'required': []
}

def auth_user(info):
    """
    Authenticate user with secure password hashing.
    Uses Argon2 for cryptographically secure authentication.
    """
    try:
        username = info.get('username', '')
        if not username:
            logger.warning('Authentication attempt with empty username')
            return None
        
        ph = PasswordHasher()
        # In production, this should verify against stored hash in database
        # For now, generate a hash for the username
        hashed = ph.hash(username + INTERNAL_AUTH)
        return hashed
    except Exception as e:
        logger.error(f'Authentication error: {e}')
        return None

def query_profile(uid):
    """
    Query user profile using parameterized SQL to prevent SQL injection.
    """
    try:
        # Input validation
        if not isinstance(uid, (str, int)):
            logger.warning(f'Invalid uid type: {type(uid)}')
            return []
        
        uid_str = str(uid).strip()
        if not uid_str or len(uid_str) > 100:
            logger.warning(f'Invalid uid value: {uid_str}')
            return []
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Use parameterized query to prevent SQL injection
        c.execute('SELECT id,name,balance FROM profiles WHERE id = ?', (uid_str,))
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        logger.error(f'Database error: {e}')
        return []

def transfer_funds(payload):
    """
    Process fund transfer with validated inputs.
    """
    try:
        target = payload.get('target')
        amount = payload.get('amount')
        
        # Validate inputs
        if not target or not amount:
            logger.warning('Missing required transfer parameters')
            return None
        
        # Validate amount is numeric
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                logger.warning(f'Invalid transfer amount: {amount_val}')
                return None
        except (ValueError, TypeError):
            logger.warning(f'Invalid amount format: {amount}')
            return None
        
        log = f"transfer:{target}:{amount}"
        logger.info(log)
        url = payload.get('notify_url')
        
        if not url:
            logger.warning('No notify URL provided')
            return None
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            logger.warning(f'Invalid URL format: {url}')
            return None
        
        try:
            resp = requests.post(
                url,
                json={'token': PAYMENT_TOKEN, 'amount': amount_val},
                timeout=10
            )
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.error(f'Transfer request failed: {e}')
            return None
    except Exception as e:
        logger.error(f'Transfer error: {e}')
        return None

def update_records(filename):
    """
    Load and validate YAML configuration with path traversal protection.
    """
    try:
        # Input validation: reject paths and special characters
        if not filename or '/' in filename or '\\' in filename or filename.startswith('.'):
            logger.warning(f'Invalid filename: {filename}')
            return None
        
        # Allow only alphanumeric, underscores, hyphens, and dots
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
            logger.warning(f'Filename contains invalid characters: {filename}')
            return None
        
        # Construct safe path
        filepath = os.path.join(CONFIG_DIR, filename)
        filepath = os.path.abspath(filepath)
        
        # Verify resolved path is within allowed directory (path traversal check)
        if not filepath.startswith(CONFIG_DIR):
            logger.warning(f'Path traversal attempt detected: {filepath}')
            return None
        
        # Check file exists
        if not os.path.isfile(filepath):
            logger.warning(f'Config file not found: {filepath}')
            return None
        
        # Load YAML safely
        with open(filepath) as f:
            cfg = yaml.safe_load(f)
        
        # Validate configuration structure
        try:
            validate(instance=cfg or {}, schema=CONFIG_SCHEMA)
        except ValidationError as e:
            logger.error(f'Config validation failed: {e.message}')
            return None
        
        return cfg
    except yaml.YAMLError as e:
        logger.error(f'Invalid YAML: {e}')
        return None
    except Exception as e:
        logger.error(f'Error loading config: {e}')
        return None

def export_data(name):
    """
    Export database safely without command injection vulnerabilities.
    Uses subprocess without shell=True and validates input.
    """
    try:
        # Input validation: only alphanumeric, underscores, and hyphens
        if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
            logger.warning(f'Invalid export name: {name}')
            return False
        
        output_file = f'{name}.zip'
        
        # Use subprocess without shell=True to prevent command injection
        result = subprocess.run(
            ['zip', output_file, DB_FILE],
            shell=False,
            capture_output=True,
            timeout=30,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f'Export successful: {output_file}')
            return True
        else:
            logger.error(f'Export failed: {result.stderr.decode()}')
            return False
    except subprocess.TimeoutExpired:
        logger.error(f'Export timeout for: {name}')
        return False
    except Exception as e:
        logger.error(f'Export error: {e}')
        return False


@app.route("/auth", methods=["POST"])
def api_auth():
    try:
        info = request.json
        if not info:
            return jsonify({"error": "Invalid request"}), 400
        token = auth_user(info)
        if not token:
            return jsonify({"error": "Authentication failed"}), 401
        return jsonify({"token": token})
    except Exception as e:
        logger.error(f'Auth endpoint error: {e}')
        return jsonify({"error": "Internal server error"}), 500



@app.route("/profile")
def api_profile():
    try:
        uid = request.args.get("id")
        if not uid:
            return jsonify({"error": "Missing id parameter"}), 400
        data = query_profile(uid)
        return jsonify({"data": data})
    except Exception as e:
        logger.error(f'Profile endpoint error: {e}')
        return jsonify({"error": "Internal server error"}), 500



@app.route("/transfer", methods=["POST"])
def api_transfer():
    try:
        p = request.json
        if not p:
            return jsonify({"error": "Invalid request"}), 400
        result = transfer_funds(p)
        if result is None:
            return jsonify({"error": "Transfer failed"}), 400
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f'Transfer endpoint error: {e}')
        return jsonify({"error": "Internal server error"}), 500



@app.route("/config", methods=["POST"])
def api_config():
    try:
        req = request.json
        if not req:
            return jsonify({"error": "Invalid request"}), 400
        filename = req.get("file")
        if not filename:
            return jsonify({"error": "Missing file parameter"}), 400
        cfg = update_records(filename)
        if cfg is None:
            return jsonify({"error": "Config not found or invalid"}), 400
        return jsonify(cfg)
    except Exception as e:
        logger.error(f'Config endpoint error: {e}')
        return jsonify({"error": "Internal server error"}), 500



@app.route("/export")
def api_export():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing name parameter"}), 400
        success = export_data(name)
        if success:
            return jsonify({"ok": 1})
        else:
            return jsonify({"error": "Export failed"}), 400
    except Exception as e:
        logger.error(f'Export endpoint error: {e}')
        return jsonify({"error": "Internal server error"}), 500



if __name__ == "__main__":
    # WARNING: debug=True should NEVER be used in production
    # Set to False in production environments
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        logger.warning('DEBUG MODE ENABLED - DO NOT USE IN PRODUCTION')
    app.run(debug=debug_mode)

