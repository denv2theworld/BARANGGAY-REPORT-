import hmac
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps

from flask import (Flask, g, jsonify, redirect, request, send_from_directory,
                   session)
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder="static", static_url_path="")

# --- Config (set these as environment variables in real use) ---
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "barangay123")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "reports.db"))
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Allow your public form (Netlify) to call this API.
# Replace with your actual Netlify URL once deployed.
CORS(app, supports_credentials=True, origins=[
    "https://baranggay-report.netlify.app",
    "http://localhost:5500",  # handy for local testing
])

ALLOWED_LOCATIONS = {"sitio munayan", "sitio bulangan", "sitio calamaisan"}
ALLOWED_STATUS = {"pending", "processing", "finished"}
MOBILE_RE = re.compile(r"^09\d{9}$")  # PH format: 09123456789


# ---------- Database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                mobile       TEXT NOT NULL,
                location     TEXT NOT NULL,
                address      TEXT NOT NULL,
                description  TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            )
            """
        )
        # older version used 'completed'
        db.execute("UPDATE reports SET status='finished' WHERE status='completed'")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- Admin auth ----------
_attempts = {}  # ip -> [timestamps]; simple brute-force limit


def too_many_attempts(ip):
    recent = [t for t in _attempts.get(ip, []) if time.time() - t < 60]
    _attempts[ip] = recent
    return len(recent) >= 5


def is_admin():
    return session.get("admin") is True


def admin_only(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not is_admin():
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*a, **kw)

    return wrapper


@app.post("/api/admin/login")
def admin_login():
    ip = request.remote_addr or "unknown"
    if too_many_attempts(ip):
        return jsonify({"error": "Too many attempts. Try again in a minute."}), 429

    password = str((request.get_json(silent=True) or {}).get("password", ""))
    if hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode()):
        session["admin"] = True
        return jsonify({"ok": True})

    _attempts.setdefault(ip, []).append(time.time())
    return jsonify({"error": "Incorrect password."}), 401


@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/admin/me")
def admin_me():
    return jsonify({"admin": is_admin()})


# ---------- Pages ----------
@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/portal.html")
def portal():
    # portal page is only served to a logged-in admin
    if not is_admin():
        return redirect("/admin.html")
    return send_from_directory(os.path.join(BASE_DIR, "protected"), "portal.html")


# ---------- Reports API ----------
@app.post("/api/reports")
def create_report():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    mobile = str(data.get("mobile", "")).strip()
    location = str(data.get("location", "")).strip().lower()
    address = str(data.get("address", "")).strip()
    description = str(data.get("description", "")).strip()

    errors = {}
    if not name:
        errors["name"] = "Name is required."
    if not MOBILE_RE.match(mobile):
        errors["mobile"] = "Enter a valid mobile number (e.g., 09123456789)."
    if location not in ALLOWED_LOCATIONS:
        errors["location"] = "Choose a valid location."
    if not address:
        errors["address"] = "Address is required."
    if not description:
        errors["description"] = "Description is required."
    if errors:
        return jsonify({"errors": errors}), 400

    ts = now()
    db = get_db()
    cur = db.execute(
        """INSERT INTO reports
           (name, mobile, location, address, description, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)""",
        (name, mobile, location, address, description, ts, ts),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "status": "pending"}), 201


@app.get("/api/reports")
@admin_only
def list_reports():
    status = request.args.get("status")
    location = request.args.get("location")
    query, params = "SELECT * FROM reports WHERE 1=1", []

    if status:
        if status not in ALLOWED_STATUS:
            return jsonify({"error": "Invalid status filter"}), 400
        query += " AND status = ?"
        params.append(status)

    if location:
        location = location.strip().lower()
        if location not in ALLOWED_LOCATIONS:
            return jsonify({"error": "Invalid location filter"}), 400
        query += " AND location = ?"
        params.append(location)

    query += " ORDER BY created_at DESC"
    db = get_db()
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/reports/<int:report_id>")
@admin_only
def get_report(report_id):
    db = get_db()
    row = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(dict(row))


@app.patch("/api/reports/<int:report_id>/status")
@admin_only
def update_report_status(report_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip().lower()
    if status not in ALLOWED_STATUS:
        return jsonify({"error": "Invalid status value"}), 400

    db = get_db()
    cur = db.execute(
        "UPDATE reports SET status = ?, updated_at = ? WHERE id = ?",
        (status, now(), report_id),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Report not found"}), 404
    return jsonify({"ok": True, "status": status})


# ---------- Entry point ----------
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
