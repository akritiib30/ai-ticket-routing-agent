"""
Resolve IQ - SQLite Database Persistence Module
Stores and manages ticket history, analysis results, manual decisions,
bulk operations, and real-time operational analytics queries.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resolve_iq.db")
SEED_MARKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".seeded_once")


def get_db_connection():
    """Create and return a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    """Initialize the tickets table and perform automatic schema migrations if needed."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            organization TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            classification TEXT NOT NULL,
            classification_confidence REAL NOT NULL,
            routing TEXT NOT NULL,
            rag_results TEXT,
            resolution TEXT NOT NULL,
            confidence REAL NOT NULL,
            confidence_tier TEXT,
            remediation TEXT,
            recurring INTEGER NOT NULL DEFAULT 0,
            recurring_details TEXT,
            escalated INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Open',
            attachment_name TEXT,
            handling_decision TEXT NOT NULL DEFAULT 'Accepted',
            resolution_ownership TEXT NOT NULL DEFAULT 'AI Resolution Available'
        )
    """)

    # Check for existing table schema migrations
    cursor.execute("PRAGMA table_info(tickets);")
    existing_columns = [col["name"] for col in cursor.fetchall()]

    if "handling_decision" not in existing_columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN handling_decision TEXT NOT NULL DEFAULT 'Accepted';")

    if "resolution_ownership" not in existing_columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN resolution_ownership TEXT NOT NULL DEFAULT 'AI Resolution Available';")

    if "subcategory" not in existing_columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN subcategory TEXT NOT NULL DEFAULT 'General';")

    if "issue_type" not in existing_columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN issue_type TEXT NOT NULL DEFAULT 'Standard Request';")

    # Normalize older statuses: change legacy 'Needs Review' or 'Escalated' to 'Open'
    cursor.execute("UPDATE tickets SET status = 'Open' WHERE status = 'Needs Review';")
    cursor.execute("UPDATE tickets SET status = 'Open', handling_decision = 'Escalated', resolution_ownership = 'Human Fix Required' WHERE status = 'Escalated';")
    cursor.execute("UPDATE tickets SET status = 'Open' WHERE status NOT IN ('Open', 'In Progress', 'Resolved', 'Closed');")

    # Synchronize handling_decision and resolution_ownership for existing rows
    cursor.execute("""
        UPDATE tickets 
        SET handling_decision = 'Escalated', resolution_ownership = 'Human Fix Required' 
        WHERE escalated = 1 AND handling_decision = 'Accepted';
    """)

    conn.commit()
    conn.close()


def parse_ticket_row(row) -> dict:
    """Convert a SQLite Row object to a clean Python dictionary with parsed JSON fields."""
    if not row:
        return None

    d = dict(row)

    # Parse JSON fields safely
    try:
        d["rag_results"] = json.loads(d["rag_results"]) if d.get("rag_results") else []
    except Exception:
        d["rag_results"] = []

    try:
        d["remediation"] = json.loads(d["remediation"]) if d.get("remediation") else {}
    except Exception:
        d["remediation"] = {"message": str(d.get("remediation", ""))}

    try:
        d["recurring_details"] = json.loads(d["recurring_details"]) if d.get("recurring_details") else {}
    except Exception:
        d["recurring_details"] = {}

    d["recurring"] = bool(d.get("recurring"))
    d["escalated"] = bool(d.get("escalated"))
    d["handling_decision"] = d.get("handling_decision") or ("Escalated" if d.get("escalated") else "Accepted")
    d["resolution_ownership"] = d.get("resolution_ownership") or ("Human Fix Required" if d.get("escalated") else "AI Resolution Available")
    d["subcategory"] = d.get("subcategory") or "General"
    d["issue_type"] = d.get("issue_type") or "Standard Request"

    return d


def save_ticket(t: dict) -> bool:
    """Save an analyzed ticket into the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    rag_json = json.dumps(t.get("rag_results", [])) if not isinstance(t.get("rag_results"), str) else t.get("rag_results")
    remediation_json = json.dumps(t.get("remediation", {})) if not isinstance(t.get("remediation"), str) else t.get("remediation")
    recurring_json = json.dumps(t.get("recurring_details", {})) if not isinstance(t.get("recurring_details"), str) else t.get("recurring_details")

    is_esc = 1 if t.get("escalated") else 0
    handling = t.get("handling_decision") or ("Escalated" if is_esc else "Accepted")
    ownership = t.get("resolution_ownership") or ("Human Fix Required" if is_esc else "AI Resolution Available")
    # A database fallback must not mark a ticket Resolved merely from AI
    # confidence. Resolution is a manual/operational outcome.
    status = t.get("status") or ("Open" if is_esc else "In Progress" if t.get("confidence_tier") == "high" else "Open")
    subcat = t.get("subcategory") or "General"
    issue = t.get("issue_type") or "Standard Request"

    cursor.execute("""
        INSERT OR REPLACE INTO tickets (
            ticket_id, timestamp, username, organization, subject, description,
            priority, category, classification, classification_confidence,
            routing, rag_results, resolution, confidence, confidence_tier,
            remediation, recurring, recurring_details, escalated, status, attachment_name,
            handling_decision, resolution_ownership, subcategory, issue_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        t.get("ticket_id"),
        t.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        t.get("username", "Unknown User"),
        t.get("organization", "Default Org"),
        t.get("subject", ""),
        t.get("description", ""),
        t.get("priority", "Medium"),
        t.get("category", "General"),
        t.get("classification", "General"),
        float(t.get("classification_confidence", 0.0)),
        t.get("routing", "General IT Support"),
        rag_json,
        t.get("resolution", ""),
        float(t.get("confidence", 0.0)),
        t.get("confidence_tier", "medium"),
        remediation_json,
        1 if t.get("recurring") else 0,
        recurring_json,
        is_esc,
        status,
        t.get("attachment_name"),
        handling,
        ownership,
        subcat,
        issue
    ))

    conn.commit()
    conn.close()
    return True


def delete_ticket(ticket_id: str) -> bool:
    """Permanently delete an individual ticket record from SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def delete_tickets_bulk(ticket_ids: list) -> int:
    """Permanently delete multiple tickets in one transaction."""
    if not ticket_ids:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ticket_ids)
    cursor.execute(f"DELETE FROM tickets WHERE ticket_id IN ({placeholders})", ticket_ids)
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def clear_all_tickets() -> int:
    """Permanently delete all stored tickets and mark that database has been cleared."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets;")
    total_before = cursor.fetchone()[0]
    cursor.execute("DELETE FROM tickets;")
    conn.commit()
    conn.close()

    # Create marker file so seed_initial_tickets_if_empty does NOT re-populate
    try:
        Path(SEED_MARKER_PATH).touch()
    except Exception:
        pass

    return total_before


def update_ticket_status(ticket_id: str, status: str) -> bool:
    """Update status of a specific ticket."""
    valid_statuses = {"Open", "In Progress", "Resolved", "Closed"}
    if status not in valid_statuses:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET status = ? WHERE ticket_id = ?", (status, ticket_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def update_ticket_decision(ticket_id: str, handling_decision: str = None, resolution_ownership: str = None) -> bool:
    """Update manual handling decision and/or resolution ownership of a ticket."""
    updates = []
    params = []

    if handling_decision:
        if handling_decision not in {"Accepted", "Escalated"}:
            return False
        updates.append("handling_decision = ?")
        params.append(handling_decision)
        # Keep escalated boolean in sync with handling_decision
        updates.append("escalated = ?")
        params.append(1 if handling_decision == "Escalated" else 0)

    if resolution_ownership:
        if resolution_ownership not in {"AI Resolution Available", "Human Fix Required"}:
            return False
        updates.append("resolution_ownership = ?")
        params.append(resolution_ownership)

    if not updates:
        return False

    params.append(ticket_id)
    query = f"UPDATE tickets SET {', '.join(updates)} WHERE ticket_id = ?"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def bulk_update_tickets(ticket_ids: list, updates: dict) -> int:
    """Bulk update status, handling_decision, and/or resolution_ownership for a list of ticket IDs."""
    if not ticket_ids or not updates:
        return 0

    sql_parts = []
    params = []

    if "status" in updates and updates["status"] in {"Open", "In Progress", "Resolved", "Closed"}:
        sql_parts.append("status = ?")
        params.append(updates["status"])

    if "handling_decision" in updates and updates["handling_decision"] in {"Accepted", "Escalated"}:
        sql_parts.append("handling_decision = ?")
        params.append(updates["handling_decision"])
        sql_parts.append("escalated = ?")
        params.append(1 if updates["handling_decision"] == "Escalated" else 0)

    if "resolution_ownership" in updates and updates["resolution_ownership"] in {"AI Resolution Available", "Human Fix Required"}:
        sql_parts.append("resolution_ownership = ?")
        params.append(updates["resolution_ownership"])

    if not sql_parts:
        return 0

    placeholders = ",".join("?" for _ in ticket_ids)
    params.extend(ticket_ids)

    query = f"UPDATE tickets SET {', '.join(sql_parts)} WHERE ticket_id IN ({placeholders})"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_all_tickets(search=None, category=None, priority=None, status=None,
                    escalation=None, department=None, handling=None, ownership=None,
                    sort_by=None):
    """Retrieve all tickets with multi-field search, filters, and custom sorting."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query += """ AND (
            LOWER(ticket_id) LIKE ? OR
            LOWER(username) LIKE ? OR
            LOWER(organization) LIKE ? OR
            LOWER(subject) LIKE ? OR
            LOWER(description) LIKE ? OR
            LOWER(category) LIKE ? OR
            LOWER(routing) LIKE ?
        )"""
        params.extend([search_pattern] * 7)

    if category and category.strip() and category.lower() != "all":
        query += " AND LOWER(category) = ?"
        params.append(category.strip().lower())

    if priority and priority.strip() and priority.lower() != "all":
        query += " AND LOWER(priority) = ?"
        params.append(priority.strip().lower())

    if status and status.strip() and status.lower() != "all":
        query += " AND LOWER(status) = ?"
        params.append(status.strip().lower())

    if department and department.strip() and department.lower() != "all":
        query += " AND LOWER(routing) = ?"
        params.append(department.strip().lower())

    if handling and handling.strip() and handling.lower() != "all":
        query += " AND LOWER(handling_decision) = ?"
        params.append(handling.strip().lower())

    if ownership and ownership.strip() and ownership.lower() != "all":
        query += " AND LOWER(resolution_ownership) = ?"
        params.append(ownership.strip().lower())

    if escalation is not None and escalation != "" and escalation.lower() != "all":
        if escalation.lower() in ("true", "1", "yes", "escalated"):
            query += " AND (escalated = 1 OR handling_decision = 'Escalated')"
        elif escalation.lower() in ("false", "0", "no", "not_escalated"):
            query += " AND (escalated = 0 AND handling_decision != 'Escalated')"

    # Sorting
    if sort_by == "oldest":
        query += " ORDER BY timestamp ASC"
    elif sort_by == "priority":
        query += """ ORDER BY 
            CASE LOWER(priority) 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                WHEN 'low' THEN 4 
                ELSE 5 
            END ASC, timestamp DESC"""
    elif sort_by == "confidence":
        query += " ORDER BY confidence DESC, timestamp DESC"
    else:
        # Default: newest first
        query += " ORDER BY timestamp DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [parse_ticket_row(r) for r in rows]


def get_ticket_by_id(ticket_id: str):
    """Fetch a single ticket by its ticket_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return parse_ticket_row(row)


def _count_successful_remediations(conn) -> int:
    """Count tickets whose stored remediation explicitly reports success."""
    cursor = conn.cursor()
    cursor.execute("SELECT remediation FROM tickets WHERE remediation IS NOT NULL AND remediation != ''")
    count = 0

    for row in cursor.fetchall():
        raw = row[0]
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

        if isinstance(data, dict) and data.get("success") is True:
            count += 1

    return count


def get_analytics_summary() -> dict:
    """Calculate aggregated metrics and distributions for the analytics dashboard."""

    conn = get_db_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------
    # Total tickets
    # ------------------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total = cursor.fetchone()[0]

    # Empty database
    if total == 0:
        conn.close()
        return {
            "total_tickets": 0,
            "open_tickets_count": 0,
            "resolved_count": 0,
            "escalated_count": 0,
            "human_fix_count": 0,
            "ai_resolution_count": 0,
            "recurring_count": 0,
            "auto_resolved_count": 0,
            "human_review_count": 0,
            "attention_count": 0,
            "escalation_rate": 0.0,
            "recurring_rate": 0.0,
            "avg_confidence": 0.0,
            "categories": {},
            "priorities": {},
            "departments": {},
            "statuses": {},
            "handling_decisions": {
                "Accepted": 0,
                "Escalated": 0
            },
            "resolution_ownerships": {
                "AI Resolution Available": 0,
                "Human Fix Required": 0
            },
            "confidence_distribution": {
                "High": 0,
                "Medium": 0,
                "Low": 0
            },
            "workload": {
                "open": 0,
                "in_progress": 0,
                "resolved": 0,
                "escalated": 0
            }
        }

    # ------------------------------------------------------------
    # Open tickets
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE status IN ('Open', 'In Progress')
    """)
    open_tickets = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Resolved tickets
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE status IN ('Resolved', 'Closed')
    """)
    resolved_count = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Escalated tickets
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE escalated = 1
           OR handling_decision = 'Escalated'
    """)
    escalated = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Human fix required
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE resolution_ownership = 'Human Fix Required'
    """)
    human_fix_count = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # AI resolution available
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE resolution_ownership = 'AI Resolution Available'
    """)
    ai_resolution_count = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Recurring tickets
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE recurring = 1
    """)
    recurring = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Average classifier confidence
    # ------------------------------------------------------------
    cursor.execute("SELECT AVG(confidence) FROM tickets")
    avg_conf = cursor.fetchone()[0] or 0.0

    # ------------------------------------------------------------
    # Category distribution
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT category, COUNT(*)
        FROM tickets
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """)
    categories = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Priority distribution
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT priority, COUNT(*)
        FROM tickets
        GROUP BY priority
        ORDER BY COUNT(*) DESC
    """)
    priorities = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Department distribution
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT routing, COUNT(*)
        FROM tickets
        GROUP BY routing
        ORDER BY COUNT(*) DESC
    """)
    departments = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Status distribution
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT status, COUNT(*)
        FROM tickets
        GROUP BY status
        ORDER BY COUNT(*) DESC
    """)
    statuses = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Handling decisions
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT handling_decision, COUNT(*)
        FROM tickets
        GROUP BY handling_decision
    """)
    handling_decisions = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Resolution ownership
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT resolution_ownership, COUNT(*)
        FROM tickets
        GROUP BY resolution_ownership
    """)
    resolution_ownerships = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    # ------------------------------------------------------------
    # Confidence distribution
    # High    >= 0.85
    # Medium  >= 0.60 and < 0.85
    # Low     < 0.60
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE confidence >= 0.85
    """)
    conf_high = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE confidence >= 0.60
          AND confidence < 0.85
    """)
    conf_med = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE confidence < 0.60
    """)
    conf_low = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Workload breakdown
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE status = 'Open'
    """)
    wl_open = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE status = 'In Progress'
    """)
    wl_in_progress = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE status IN ('Resolved', 'Closed')
    """)
    wl_resolved = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE handling_decision = 'Escalated'
           OR escalated = 1
    """)
    wl_escalated = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Tickets needing attention
    # ------------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(DISTINCT ticket_id)
        FROM tickets
        WHERE handling_decision = 'Escalated'
           OR resolution_ownership = 'Human Fix Required'
           OR confidence < 0.60
           OR escalated = 1
    """)
    attention_count = cursor.fetchone()[0]

    # ------------------------------------------------------------
    # Rates
    # ------------------------------------------------------------
    escalation_rate = (
        round((escalated / total) * 100, 1)
        if total > 0 else 0.0
    )

    recurring_rate = (
        round((recurring / total) * 100, 1)
        if total > 0 else 0.0
    )

    # ------------------------------------------------------------
    # IMPORTANT:
    # Count successful remediation BEFORE closing the connection.
    # This fixes:
    # sqlite3.ProgrammingError:
    # Cannot operate on a closed database.
    # ------------------------------------------------------------
    successful_remediations = _count_successful_remediations(conn)

    # Close database only after ALL queries are complete.
    conn.close()

    # ------------------------------------------------------------
    # Return analytics object
    # ------------------------------------------------------------
    return {
        "total_tickets": total,

        "open_tickets_count": open_tickets,

        "resolved_count": resolved_count,

        # This counts only tickets whose stored remediation
        # explicitly reports success=True.
        "auto_resolved_count": successful_remediations,

        "escalated_count": escalated,

        "human_fix_count": human_fix_count,

        "ai_resolution_count": ai_resolution_count,

        "human_review_count": human_fix_count,

        "attention_count": attention_count,

        "recurring_count": recurring,

        "escalation_rate": escalation_rate,

        "recurring_rate": recurring_rate,

        "avg_confidence": round(float(avg_conf), 4),

        "workload": {
            "open": wl_open,
            "in_progress": wl_in_progress,
            "resolved": wl_resolved,
            "escalated": wl_escalated
        },

        "categories": categories,

        "priorities": priorities,

        "departments": departments,

        "statuses": statuses,

        "handling_decisions": handling_decisions,

        "resolution_ownerships": resolution_ownerships,

        "confidence_distribution": {
            "High": conf_high,
            "Medium": conf_med,
            "Low": conf_low
        }
    }

def seed_initial_tickets_if_empty(force: bool = False):
    """
    Seed initial historical demonstration tickets ONLY if database has never been seeded.
    If the user intentionally clears the database, this marker prevents unwanted re-seeding,
    unless force=True is explicitly specified.
    """
    if not force and os.path.exists(SEED_MARKER_PATH):
        return  # Was previously initialized/cleared, respect user data

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0 and not force:
        try:
            Path(SEED_MARKER_PATH).touch()
        except Exception:
            pass
        return

    seed_samples = [
        {
            "ticket_id": "TKT-NET-1042",
            "timestamp": "2026-09-08 09:14:22",
            "username": "Alex Rivera",
            "organization": "Nexus Corp",
            "subject": "VPN connection drops frequently",
            "description": "VPN connection disconnects every 15 minutes when connecting from home office.",
            "priority": "High",
            "category": "Network",
            "classification": "Network",
            "classification_confidence": 0.9136,
            "routing": "Network Support",
            "rag_results": [
                {"ticket_id": "T0042", "text": "VPN tunnel failure on corporate gateway", "similarity": 0.45, "resolution": "Reset local network adapter and reconnect using primary SSL tunnel endpoint."},
                {"ticket_id": "T0088", "text": "Intermittent network timeouts on VPN", "similarity": 0.38, "resolution": "Updated DNS settings and flushed local DNS resolver cache."}
            ],
            "resolution": "Reset network adapter, flush local DNS cache, and reconnect through the secondary regional VPN gateway.",
            "confidence": 0.9136,
            "confidence_tier": "high",
            "remediation": {"diagnosis": "VPN gateway reconnect timeout", "action": "Adapter diagnostic test executed", "success": True, "message": "Local adapter diagnostics passed. Gateway route verified."},
            "recurring": 1,
            "recurring_details": {"is_recurring": True, "cluster_size": 3},
            "escalated": 0,
            "status": "Resolved",
            "attachment_name": None,
            "handling_decision": "Accepted",
            "resolution_ownership": "AI Resolution Available"
        },
        {
            "ticket_id": "TKT-ACC-2091",
            "timestamp": "2026-09-08 11:30:05",
            "username": "Sarah Chen",
            "organization": "Horizon Tech",
            "subject": "Password reset token expired",
            "description": "Unable to log into internal ERP system, password expired and reset email link failed.",
            "priority": "Medium",
            "category": "Access Management",
            "classification": "Access Management",
            "classification_confidence": 0.8889,
            "routing": "Identity & Access Management",
            "rag_results": [
                {"ticket_id": "T0105", "text": "ERP account locked after invalid attempts", "similarity": 0.50, "resolution": "Admin triggered single-use MFA verification link via registered phone."}
            ],
            "resolution": "Trigger automated self-service SSO identity verification link or contact IAM administrator.",
            "confidence": 0.8889,
            "confidence_tier": "high",
            "remediation": {"diagnosis": "Account credential policy enforcement", "action": "Policy safety boundary applied", "success": False, "message": "Credentials and security modifications require explicit human IAM authorization."},
            "recurring": 0,
            "recurring_details": {"is_recurring": False, "cluster_size": 1},
            "escalated": 0,
            "status": "Open",
            "attachment_name": None,
            "handling_decision": "Accepted",
            "resolution_ownership": "Human Fix Required"
        },
        {
            "ticket_id": "TKT-APP-3310",
            "timestamp": "2026-09-08 14:02:40",
            "username": "Marcus Vance",
            "organization": "Atlas Media",
            "subject": "Internal reporting dashboard crash on export",
            "description": "The analytics reporting tool throws an unhandled OutOfMemoryException whenever exporting more than 5,000 rows.",
            "priority": "High",
            "category": "Application",
            "classification": "Application",
            "classification_confidence": 0.7824,
            "routing": "Application Support",
            "rag_results": [
                {"ticket_id": "T0215", "text": "Report export timeout for large tables", "similarity": 0.40, "resolution": "Streamed result set chunked in background worker queue."}
            ],
            "resolution": "Utilize chunked background batch exporter or reduce query date range.",
            "confidence": 0.7824,
            "confidence_tier": "medium",
            "remediation": {"diagnosis": "Application process memory limit", "action": "Checked process health", "success": True, "message": "Worker service is responding; export buffer limit reached."},
            "recurring": 1,
            "recurring_details": {"is_recurring": True, "cluster_size": 3},
            "escalated": 0,
            "status": "In Progress",
            "attachment_name": "crash_dump_log.txt",
            "handling_decision": "Accepted",
            "resolution_ownership": "AI Resolution Available"
        },
        {
            "ticket_id": "TKT-SEC-4402",
            "timestamp": "2026-09-08 16:45:12",
            "username": "Elena Rostova",
            "organization": "FinEdge Global",
            "subject": "Suspicious login alert from unknown IP",
            "description": "Received automated notification about an unauthorized login attempt from a foreign country at 3 AM.",
            "priority": "Critical",
            "category": "Security",
            "classification": "Security",
            "classification_confidence": 0.6329,
            "routing": "Security Operations",
            "rag_results": [
                {"ticket_id": "T0301", "text": "Anomalous geographic login attempt", "similarity": 0.52, "resolution": "Immediately revoked all active session tokens and enforced MFA re-enrollment."}
            ],
            "resolution": "Immediately revoke active user session tokens, lock account, and initiate SOC threat assessment.",
            "confidence": 0.6329,
            "confidence_tier": "medium",
            "remediation": {"diagnosis": "Potential account compromise indicator", "action": "Security policy restriction active", "success": False, "message": "Security events require Tier-2 SOC verification."},
            "recurring": 0,
            "recurring_details": {"is_recurring": False, "cluster_size": 1},
            "escalated": 1,
            "status": "Open",
            "attachment_name": None,
            "handling_decision": "Escalated",
            "resolution_ownership": "Human Fix Required"
        }
    ]

    for sample in seed_samples:
        save_ticket(sample)

    try:
        Path(SEED_MARKER_PATH).touch()
    except Exception:
        pass


# Initialize DB on module import
init_db()
seed_initial_tickets_if_empty()
