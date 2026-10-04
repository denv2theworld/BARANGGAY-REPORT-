from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import sqlite3

app = FastAPI(title="Barangay 123 Issue Report API")

# Allow your frontend to call this API.
# For local testing with index.html opened directly ("*" is fine).
# For production, replace "*" with your actual frontend domain, e.g.:
# allow_origins=["https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "issues.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            location TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


# ---- Request/response models ----
class IssueCreate(BaseModel):
    name: str
    mobile: str
    location: str
    address: str
    description: str


class Issue(IssueCreate):
    id: int
    status: str
    created_at: str


# ---- Routes ----
@app.post("/api/issues", response_model=Issue, status_code=201)
def create_issue(issue: IssueCreate):
    if len(issue.description.strip()) < 5:
        raise HTTPException(status_code=400, detail="Description is too short")
    if not issue.name.strip() or not issue.mobile.strip() or not issue.address.strip():
        raise HTTPException(status_code=400, detail="Missing required fields")

    created_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO issues (name, mobile, location, address, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (issue.name, issue.mobile, issue.location, issue.address, issue.description, created_at),
    )
    conn.commit()
    issue_id = cur.lastrowid
    conn.close()

    return Issue(
        id=issue_id,
        status="pending",
        created_at=created_at,
        **issue.model_dump(),
    )


@app.get("/api/issues", response_model=list[Issue])
def list_issues(status: str | None = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if status:
        rows = conn.execute("SELECT * FROM issues WHERE status = ?", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM issues ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/issues/{issue_id}", response_model=Issue)
def get_issue(issue_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return dict(row)


@app.patch("/api/issues/{issue_id}/status")
def update_status(issue_id: int, status: str):
    if status not in {"pending", "in_progress", "resolved"}:
        raise HTTPException(status_code=400, detail="Invalid status value")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("UPDATE issues SET status = ? WHERE id = ?", (status, issue_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"message": "Status updated"}
