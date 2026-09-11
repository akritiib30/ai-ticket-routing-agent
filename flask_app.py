"""
Resolve IQ - Production Multi-Page Flask Web Application
AI-Powered Intelligent Ticket Routing & Resolution System
"""

import os
import re
import secrets
import uuid
import urllib.parse
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    Response,
    send_from_directory,
)

from agent.pipeline import TicketAgentPipeline
from agent.routing import ROUTING_MAP
import database
import reports

app = Flask(__name__)

# Set the SECRET_KEY environment variable for a real deployment so sessions
# survive a restart. Without it, we generate a random key at startup instead
# of shipping a fixed string in source control — a baked-in secret lets
# anyone who reads the code forge session cookies.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Directory for file attachments
ATTACHMENTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "attachments"
)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Initialize AI Pipeline
pipeline = TicketAgentPipeline()


# ============================================================
# CATEGORY & ROUTING NORMALIZATION
# ============================================================

# Friendly UI category labels -> canonical classifier/storage labels.
# The application accepts the current labels used by the UI and a small set
# of legacy labels so older tickets continue to work correctly.
CATEGORY_ALIASES = {
    "Network & Connectivity": "Network",
    "Account & Access": "Access Management",
    "Email & Collaboration": "Email",
    "Software & Applications": "Application",
    "Infrastructure & Servers": "Infrastructure",
    "Database & Storage": "Database",
    "Hardware & Peripherals": "Hardware",
    "Storage & Files": "Storage",
    "Security Operations": "Security",

    # Backward-compatible legacy label.
    "Security & Compliance": "Security",
}

DEPARTMENT_MAP = {
    "Network": "Network Support",
    "Access Management": "Identity & Access Management",
    "Application": "Application Support",
    "Security": "Security Operations",
    "Database": "Database Operations",
    "Infrastructure": "Infrastructure Support",
    "Hardware": "End-User Computing",
    "Email": "Collaboration Support",
    "Storage": "Storage & Infrastructure Support",
}


def get_greeting():
    """Return friendly time-of-day greeting."""
    hour = datetime.now().hour

    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# ============================================================
# MULTI-PAGE APPLICATION ROUTES
# ============================================================

@app.route("/")
def home():
    """Root route: redirect to dashboard if logged in, else to login."""
    if "user" not in session:
        return redirect(url_for("login"))

    return redirect(url_for("dashboard_page"))


@app.route("/dashboard")
def dashboard_page():
    """Dedicated Command Center Dashboard."""
    if "user" not in session:
        return redirect(url_for("home"))

    analytics = database.get_analytics_summary()
    all_tickets = database.get_all_tickets()
    recent_tickets = all_tickets[:5]

    # Tickets specifically needing attention:
    # escalated, human fix required, critical/high open, or low confidence.
    attention_tickets = [
        t for t in all_tickets
        if t.get("status") not in ("Resolved", "Closed")
        and (
            t.get("handling_decision") == "Escalated"
            or t.get("escalated")
            or t.get("resolution_ownership") == "Human Fix Required"
            or t.get("priority") in ("Critical", "High")
            or (
                t.get("confidence") is not None
                and float(t.get("confidence")) < 0.60
            )
        )
    ][:5]

    # Dynamic insight based on database state.
    top_categories = sorted(
        (analytics.get("categories") or {}).items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_cat_name = top_categories[0][0] if top_categories else "Support"
    attention_count = len(attention_tickets)
    avg_conf_pct = round(
        (analytics.get("avg_confidence") or 0.0) * 100
    )

    return render_template(
        "dashboard.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="dashboard",
        greeting=get_greeting(),
        analytics=analytics,
        recent_tickets=recent_tickets,
        attention_tickets=attention_tickets,
        attention_count=attention_count,
        top_cat_name=top_cat_name,
        avg_conf_pct=avg_conf_pct
    )


@app.route("/submit-ticket")
def submit_ticket_page():
    """Dedicated Submit Ticket Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "submit_ticket.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="submit"
    )


@app.route("/ticket-queue")
def ticket_queue_page():
    """Dedicated Ticket Queue Operations Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    category = request.args.get("category")
    priority = request.args.get("priority")
    status = request.args.get("status")
    escalation = request.args.get("escalation")
    department = request.args.get("department")
    handling = request.args.get("handling")
    ownership = request.args.get("ownership")
    search = request.args.get("search")
    sort_by = request.args.get("sort_by")

    tickets = database.get_all_tickets(
        search=search,
        category=category,
        priority=priority,
        status=status,
        escalation=escalation,
        department=department,
        handling=handling,
        ownership=ownership,
        sort_by=sort_by
    )

    return render_template(
        "ticket_queue.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="queue",
        tickets=tickets
    )


@app.route("/ticket/<ticket_id>")
def ticket_detail_page(ticket_id):
    """Dedicated Individual Ticket Details Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    ticket = database.get_ticket_by_id(ticket_id)

    if not ticket:
        return redirect(url_for("ticket_queue_page"))

    return render_template(
        "ticket_detail.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="queue",
        ticket=ticket
    )


@app.route("/analytics")
def analytics_page():
    """Dedicated Support Operations Analytics Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    analytics = database.get_analytics_summary()

    return render_template(
        "analytics.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="analytics",
        analytics=analytics
    )


@app.route("/ai-overview")
@app.route("/ai-pipeline")
def ai_pipeline_page():
    """Dedicated AI Architecture Overview Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "ai_pipeline.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="pipeline"
    )


@app.route("/ai-pipeline/classification")
def pipeline_classification_page():
    """Classification Intelligence Deep-Dive Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    analytics = database.get_analytics_summary()
    recent_tickets = database.get_all_tickets()[:6]

    return render_template(
        "pipeline_classification.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="classification",
        analytics=analytics,
        recent_tickets=recent_tickets
    )


@app.route("/knowledge")
@app.route("/ai-pipeline/rag")
def pipeline_rag_page():
    """Dedicated Knowledge Retrieval Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    tickets = database.get_all_tickets()
    recent_rag_examples = []

    for t in tickets:
        if t.get("rag_results") and len(t["rag_results"]) > 0:
            recent_rag_examples.append({
                "parent_ticket_id": t["ticket_id"],
                "parent_subject": t["subject"],
                "rag_results": t["rag_results"]
            })

        if len(recent_rag_examples) >= 4:
            break

    return render_template(
        "pipeline_rag.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="rag",
        recent_rag_examples=recent_rag_examples
    )


@app.route("/confidence")
@app.route("/ai-pipeline/confidence")
def pipeline_confidence_page():
    """Dedicated Decision Confidence Intelligence Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    analytics = database.get_analytics_summary()

    return render_template(
        "pipeline_confidence.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="confidence",
        analytics=analytics
    )


@app.route("/escalation")
@app.route("/ai-pipeline/escalation")
def pipeline_escalation_page():
    """Dedicated Human Escalation & Safeguards Page."""
    if "user" not in session:
        return redirect(url_for("home"))

    analytics = database.get_analytics_summary()
    all_tickets = database.get_all_tickets()

    escalated_tickets = [
        t for t in all_tickets
        if t.get("escalated")
        or t.get("handling_decision") == "Escalated"
    ][:6]

    return render_template(
        "pipeline_escalation.html",
        username=session["user"],
        organization=session.get("organization", "Default Org"),
        active_page="escalation",
        analytics=analytics,
        escalated_tickets=escalated_tickets
    )


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle Resolve IQ workspace sign-in.

    The current project uses a lightweight workspace sign-in rather than a
    full user-account authentication system. The form therefore requires
    username, password, and organization values, but the password is not
    stored and is not independently verified because this application does
    not currently contain a user/password database.
    """

    if request.method == "GET":
        if "user" in session:
            return redirect(url_for("dashboard_page"))

        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    organization = request.form.get("organization", "").strip()

    if not username:
        return render_template(
            "login.html",
            error="Please enter your username to continue."
        )

    if not password:
        return render_template(
            "login.html",
            error="Please enter your password to continue."
        )

    if not organization:
        return render_template(
            "login.html",
            error="Please enter your company or organization name."
        )

    # Establish a lightweight workspace session.
    # Never store the password.
    session["user"] = username
    session["organization"] = organization

    return redirect(url_for("dashboard_page"))


@app.route("/clear-session")
@app.route("/logout")
def logout():
    """Clear user session and redirect to login."""
    session.clear()

    return redirect(url_for("home"))


@app.route("/dev-login")
def dev_login():
    """
    Developer and visual testing helper route.

    Only available when debug=True. This route lets a developer establish
    a test session without credentials, so it must never be reachable on
    a real deployment with debug disabled.
    """

    if not app.debug:
        return jsonify({
            "success": False,
            "error": "Not found."
        }), 404

    session["user"] = request.args.get(
        "user",
        "Akriti Biswas"
    )

    session["organization"] = request.args.get(
        "org",
        "Resolve IQ Corp"
    )

    redirect_target = request.args.get(
        "next",
        "/dashboard"
    )

    extra_params = {
        k: v
        for k, v in request.args.items()
        if k not in ("user", "org", "next")
    }

    if extra_params:
        sep = "&" if "?" in redirect_target else "?"
        redirect_target += (
            f"{sep}{urllib.parse.urlencode(extra_params)}"
        )

    return redirect(redirect_target)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():
    """Health check endpoint verifying app and database connectivity."""

    db_status = "connected"

    try:
        conn = database.get_db_connection()
        conn.execute("SELECT 1;").fetchone()
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    is_healthy = db_status == "connected"
    status_code = 200 if is_healthy else 503

    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "Resolve IQ",
        "version": "2.0.0",
        "database": db_status,
        "message": "Resolve IQ Flask backend is running"
    }), status_code


# ============================================================
# TICKET ANALYSIS (AI PIPELINE)
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_ticket():
    """
    Main AI ticket analysis endpoint.

    Accepts JSON or multipart/form-data with optional file upload.
    Executes TicketAgentPipeline, persists the result to SQLite,
    and returns structured JSON.
    """

    try:
        attachment_name = None

        # ----------------------------------------------------
        # Read JSON request
        # ----------------------------------------------------
        if request.is_json:
            data = request.get_json(silent=True) or {}

            subject = data.get("subject", "").strip()

            description = (
                data.get("text", "")
                or data.get("description", "").strip()
            )

            user = (
                data.get("user")
                or session.get("user", "Anonymous")
            )

            priority = data.get(
                "priority",
                "Auto Detect"
            )

            selected_category = data.get(
                "category",
                ""
            )

        # ----------------------------------------------------
        # Read multipart/form-data request
        # ----------------------------------------------------
        else:
            subject = request.form.get(
                "subject",
                ""
            ).strip()

            description = (
                request.form.get(
                    "description",
                    ""
                ).strip()
                or request.form.get(
                    "text",
                    ""
                ).strip()
            )

            user = (
                request.form.get(
                    "username",
                    ""
                ).strip()
                or session.get(
                    "user",
                    "Anonymous"
                )
            )

            priority = request.form.get(
                "priority",
                "Auto Detect"
            )

            selected_category = request.form.get(
                "category",
                ""
            )

            # File upload handling
            if "attachment" in request.files:
                file = request.files["attachment"]

                if file and file.filename:
                    orig_name = file.filename
                    safe_name = secure_filename(orig_name)

                    stored_name = (
                        f"{uuid.uuid4().hex[:6]}_"
                        f"{safe_name}"
                    )

                    file.save(
                        os.path.join(
                            ATTACHMENTS_DIR,
                            stored_name
                        )
                    )

                    attachment_name = orig_name

        # ----------------------------------------------------
        # Validate ticket content
        # ----------------------------------------------------
        if not subject and not description:
            return jsonify({
                "success": False,
                "error": "Ticket subject or description is required."
            }), 400

        # ----------------------------------------------------
        # Combine subject + description
        # ----------------------------------------------------
        ticket_text = subject

        if description and subject:
            ticket_text += ". "

        ticket_text += description

        # ----------------------------------------------------
        # Generate unique ticket ID
        # ----------------------------------------------------
        ticket_id = (
            "TKT-"
            + uuid.uuid4().hex[:8].upper()
        )

        now_str = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        user_org = session.get(
            "organization",
            "Nexus Corp"
        )

        # ----------------------------------------------------
        # Run EXISTING AI PIPELINE
        # ----------------------------------------------------
        result = pipeline.run(
            ticket_id=ticket_id,
            raw_text=ticket_text,
            user=user
        )

        # ----------------------------------------------------
        # Extract classification + confidence
        # ----------------------------------------------------
        classification = result.classification

        pred_category = getattr(
            classification,
            "category",
            str(classification)
        )

        pred_confidence = float(
            getattr(
                classification,
                "confidence",
                0.0
            )
        )

        pred_subcategory = getattr(
            classification,
            "subcategory",
            "General"
        ) or "General"

        pred_issue_type = getattr(
            classification,
            "issue_type",
            "Standard Request"
        ) or "Standard Request"

        # ----------------------------------------------------
        # Handle manual category selection
        # ----------------------------------------------------
        if (
            selected_category
            and selected_category.strip()
            and selected_category not in (
                "AI will classify",
                "AI Detect"
            )
        ):
            final_category = CATEGORY_ALIASES.get(
                selected_category.strip(),
                selected_category.strip()
            )

            dept_override = DEPARTMENT_MAP.get(
                final_category,
                ROUTING_MAP.get(final_category)
            )

            routing_dept = (
                dept_override
                if dept_override
                else result.routing.department
            )

        else:
            final_category = pred_category
            routing_dept = result.routing.department

        # ----------------------------------------------------
        # Auto-detect Priority
        # ----------------------------------------------------
        final_priority = priority

        if not priority or priority in (
            "Auto Detect",
            "Auto-detect priority",
            "Auto"
        ):
            text_l = ticket_text.lower()

            urgent_keywords = [
                "urgent",
                "asap",
                "emergency",
                "critical",
                "immediately",
                "outage",
                "crash"
            ]

            if any(
                keyword in text_l
                for keyword in urgent_keywords
            ):
                final_priority = "Critical"

            elif (
                final_category in (
                    "Security",
                    "Security Operations"
                )
                or result.escalated
            ):
                final_priority = "High"

            elif result.confidence.tier == "high":
                final_priority = "Low"

            else:
                final_priority = "Medium"

        # ----------------------------------------------------
        # Determine Handling Decision
        # ----------------------------------------------------
        handling_decision = (
            "Escalated"
            if result.escalated
            else "Accepted"
        )

        # ----------------------------------------------------
        # Determine Resolution Ownership
        # ----------------------------------------------------
        if (
            result.escalated
            or result.confidence.tier == "low"
        ):
            resolution_ownership = "Human Fix Required"
        else:
            resolution_ownership = "AI Resolution Available"

        # ----------------------------------------------------
        # Determine Ticket Status
        # ----------------------------------------------------
        # A new ticket is NOT marked Resolved merely because
        # a diagnostic succeeded.
        #
        # Resolution must be confirmed by an operator/user.
        if result.escalated:
            ticket_status = "Open"

        elif result.confidence.tier == "high":
            ticket_status = "In Progress"

        else:
            ticket_status = "Open"

        # ----------------------------------------------------
        # Format retrieved RAG tickets
        # ----------------------------------------------------
        retrieved_list = []

        for item in result.retrieved:
            retrieved_list.append({
                "ticket_id": getattr(
                    item,
                    "ticket_id",
                    ""
                ),
                "text": getattr(
                    item,
                    "text",
                    ""
                ),
                "similarity": round(
                    float(
                        getattr(
                            item,
                            "similarity",
                            0.0
                        )
                    ),
                    4
                ),
                "resolution": getattr(
                    item,
                    "resolution",
                    ""
                )
            })

        # ----------------------------------------------------
        # Save record to SQLite
        # ----------------------------------------------------
        ticket_record = {
            "ticket_id": ticket_id,
            "timestamp": now_str,
            "username": user,
            "organization": user_org,
            "subject": (
                subject
                if subject
                else ticket_text[:60]
            ),
            "description": (
                description
                if description
                else subject
            ),
            "priority": final_priority,
            "category": final_category,
            "subcategory": pred_subcategory,
            "issue_type": pred_issue_type,
            "classification": pred_category,
            "classification_confidence": pred_confidence,
            "routing": routing_dept,
            "rag_results": retrieved_list,
            "resolution": result.resolution.suggested_steps,
            "confidence": result.confidence.score,
            "confidence_tier": result.confidence.tier,
            "remediation": result.remediation,
            "recurring": result.recurring.is_recurring,
            "recurring_details": {
                "is_recurring": (
                    result.recurring.is_recurring
                ),
                "cluster_size": (
                    result.recurring.cluster_size
                )
            },
            "escalated": result.escalated,
            "status": ticket_status,
            "handling_decision": handling_decision,
            "resolution_ownership": resolution_ownership,
            "attachment_name": attachment_name
        }

        database.save_ticket(ticket_record)

        # ----------------------------------------------------
        # Return structured JSON
        # ----------------------------------------------------
        return jsonify({
            "success": True,
            "ticket_id": ticket_id,

            "ticket": {
                "id": ticket_id,
                "user": user,
                "organization": user_org,
                "subject": ticket_record["subject"],
                "description": ticket_record["description"],
                "priority": final_priority,
                "category": final_category,
                "subcategory": pred_subcategory,
                "issue_type": pred_issue_type,
                "attachment_name": attachment_name,
                "timestamp": now_str
            },

            "classification": {
                "category": pred_category,
                "subcategory": pred_subcategory,
                "issue_type": pred_issue_type,
                "confidence": pred_confidence
            },

            "routing": {
                "department": routing_dept
            },

            "rag": {
                "results": retrieved_list
            },

            "resolution": {
                "suggestion": (
                    result.resolution.suggested_steps
                )
            },

            "confidence": {
                "score": result.confidence.score,
                "tier": result.confidence.tier
            },

            "remediation": result.remediation,

            "recurring": {
                "is_recurring": (
                    result.recurring.is_recurring
                ),
                "cluster_size": (
                    result.recurring.cluster_size
                )
            },

            "escalated": result.escalated,
            "status": ticket_status,
            "handling_decision": handling_decision,
            "resolution_ownership": resolution_ownership
        })

    except Exception as e:
        import traceback

        print("PIPELINE ERROR:")
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": (
                "An error occurred while analyzing "
                f"the ticket: {str(e)}"
            )
        }), 500


# ============================================================
# TICKET QUEUE, HISTORY & MUTATION APIs
# ============================================================

@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    """Retrieve tickets with search and filter parameters."""

    search = request.args.get("search")
    category = request.args.get("category")
    priority = request.args.get("priority")
    status = request.args.get("status")
    escalation = request.args.get("escalation")
    department = request.args.get("department")
    handling = request.args.get("handling")
    ownership = request.args.get("ownership")
    sort_by = request.args.get("sort_by")

    tickets = database.get_all_tickets(
        search=search,
        category=category,
        priority=priority,
        status=status,
        escalation=escalation,
        department=department,
        handling=handling,
        ownership=ownership,
        sort_by=sort_by
    )

    return jsonify({
        "success": True,
        "count": len(tickets),
        "tickets": tickets
    })


@app.route("/api/tickets/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Retrieve full details of a specific ticket."""

    ticket = database.get_ticket_by_id(ticket_id)

    if not ticket:
        return jsonify({
            "success": False,
            "error": f"Ticket {ticket_id} not found."
        }), 404

    return jsonify({
        "success": True,
        "ticket": ticket
    })


@app.route("/api/tickets/<ticket_id>", methods=["DELETE"])
def delete_single_ticket(ticket_id):
    """
    Permanently delete an individual ticket and safely clean
    up its attachment if present.
    """

    ticket = database.get_ticket_by_id(ticket_id)

    if not ticket:
        return jsonify({
            "success": False,
            "error": f"Ticket {ticket_id} not found."
        }), 404

    # Remove attachment file if it exists.
    #
    # attachment_name stores the original display filename,
    # while the actual file on disk uses secure_filename().
    if ticket.get("attachment_name"):
        try:
            safe_disp_name = secure_filename(
                ticket["attachment_name"]
            )

            for fname in os.listdir(
                ATTACHMENTS_DIR
            ):
                if fname.endswith(safe_disp_name):
                    fpath = os.path.join(
                        ATTACHMENTS_DIR,
                        fname
                    )

                    if os.path.exists(fpath):
                        os.remove(fpath)

        except Exception as e:
            print(
                "Attachment file deletion warning: "
                f"{e}"
            )

    deleted = database.delete_ticket(ticket_id)

    return jsonify({
        "success": deleted,
        "ticket_id": ticket_id,
        "message": (
            f"Ticket {ticket_id} deleted successfully."
        )
    })


@app.route("/api/tickets", methods=["DELETE"])
def clear_all_tickets():
    """Clear all tickets and remove stored attachments."""

    deleted_count = database.clear_all_tickets()

    # Clean attachments folder.
    try:
        for fname in os.listdir(
            ATTACHMENTS_DIR
        ):
            fpath = os.path.join(
                ATTACHMENTS_DIR,
                fname
            )

            if os.path.isfile(fpath):
                os.remove(fpath)

    except Exception as e:
        print(
            "Attachments cleanup warning: "
            f"{e}"
        )

    return jsonify({
        "success": True,
        "deleted_count": deleted_count,
        "message": (
            f"All {deleted_count} tickets have "
            "been permanently cleared."
        )
    })


@app.route("/api/tickets/bulk-delete", methods=["POST"])
def bulk_delete_tickets():
    """Permanently delete multiple tickets."""

    data = request.get_json(silent=True) or {}
    ticket_ids = data.get("ticket_ids", [])

    if not ticket_ids or not isinstance(
        ticket_ids,
        list
    ):
        return jsonify({
            "success": False,
            "error": "No valid ticket IDs provided."
        }), 400

    deleted_count = database.delete_tickets_bulk(
        ticket_ids
    )

    return jsonify({
        "success": True,
        "deleted_count": deleted_count,
        "message": (
            f"Successfully deleted "
            f"{deleted_count} tickets."
        )
    })


@app.route(
    "/api/tickets/<ticket_id>/status",
    methods=["PATCH"]
)
def update_ticket_status(ticket_id):
    """
    Update ticket status.

    Allowed:
    Open
    In Progress
    Resolved
    Closed
    """

    data = request.get_json(silent=True) or {}
    status = data.get("status")

    allowed_statuses = {
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    }

    if not status or status not in allowed_statuses:
        return jsonify({
            "success": False,
            "error": (
                "Invalid status. Allowed: "
                "Open, In Progress, Resolved, Closed."
            )
        }), 400

    updated = database.update_ticket_status(
        ticket_id,
        status
    )

    if not updated:
        return jsonify({
            "success": False,
            "error": (
                f"Ticket {ticket_id} not found."
            )
        }), 404

    return jsonify({
        "success": True,
        "ticket_id": ticket_id,
        "status": status
    })


@app.route(
    "/api/tickets/<ticket_id>/decision",
    methods=["PATCH"]
)
def update_ticket_decision(ticket_id):
    """
    Update manual handling decision and/or
    resolution ownership.
    """

    data = request.get_json(silent=True) or {}

    handling = data.get(
        "handling_decision"
    )

    ownership = data.get(
        "resolution_ownership"
    )

    updated = database.update_ticket_decision(
        ticket_id,
        handling,
        ownership
    )

    if not updated:
        return jsonify({
            "success": False,
            "error": (
                f"Failed to update decision "
                f"for {ticket_id}."
            )
        }), 400

    return jsonify({
        "success": True,
        "ticket_id": ticket_id,
        "handling_decision": handling,
        "resolution_ownership": ownership
    })


@app.route(
    "/api/tickets/bulk-update",
    methods=["POST"]
)
def bulk_update_tickets():
    """
    Bulk update status, handling decision,
    or resolution ownership.
    """

    data = request.get_json(silent=True) or {}

    ticket_ids = data.get(
        "ticket_ids",
        []
    )

    updates = data.get(
        "updates",
        {}
    )

    if not ticket_ids or not updates:
        return jsonify({
            "success": False,
            "error": (
                "Missing ticket_ids or "
                "update parameters."
            )
        }), 400

    updated_count = database.bulk_update_tickets(
        ticket_ids,
        updates
    )

    return jsonify({
        "success": True,
        "updated_count": updated_count,
        "message": (
            f"Updated {updated_count} tickets."
        )
    })


# ============================================================
# AI ASSISTANT CHATBOT API
# ============================================================

def generate_assistant_reply(
    message: str,
    ticket_id: str = None
) -> dict:
    """
    Contextual, grounded AI Assistant engine.

    Explains ticket details, classification rationale,
    confidence calibration, escalation decisions,
    recommended resolutions, or platform questions.
    """

    msg_clean = message.strip()
    msg_lower = msg_clean.lower()

    # Check for ticket reference in text if not explicitly provided.
    referenced_tid = ticket_id

    if not referenced_tid:
        match = re.search(
            r"(TKT-[A-Za-z0-9-]+)",
            msg_clean,
            re.I
        )

        if match:
            referenced_tid = match.group(1).upper()

    # ========================================================
    # CASE A: TICKET CONTEXT
    # ========================================================

    if referenced_tid:

        t = database.get_ticket_by_id(
            referenced_tid
        )

        if not t:
            return {
                "reply": (
                    "I checked our SQLite records, but "
                    f"couldn't find a ticket matching "
                    f"**{referenced_tid}**. Please verify "
                    "the Ticket ID."
                ),
                "ticket_id": referenced_tid
            }

        remed = t.get("remediation") or {}

        conf_pct = round(
            t.get("confidence", 0.0) * 100,
            1
        )

        # ----------------------------------------------------
        # 1. Classification inquiry
        # ----------------------------------------------------
        if any(
            w in msg_lower
            for w in [
                "why classified",
                "classification",
                "category",
                "classified"
            ]
        ):
            return {
                "reply": (
                    f"### Classification Analysis for "
                    f"**{t['ticket_id']}**\n\n"

                    f"- **Category:** `{t['category']}`\n"
                    f"- **Model Probability:** "
                    f"`{round(t.get('classification_confidence', 0) * 100, 1)}%`\n"
                    f"- **Routing Department:** "
                    f"`{t['routing']}`\n\n"

                    f"**How the AI determined this:**\n"

                    f"The scikit-learn TF-IDF classifier "
                    f"analyzed the ticket subject and description "
                    f"for domain indicators. "

                    f"Phrases like "
                    f"*\"{t['subject'][:50]}\"* "
                    f"matched historical feature patterns "
                    f"associated with `{t['category']}` incidents, "

                    f"leading to an intelligent routing "
                    f"recommendation for the "
                    f"**{t['routing']}** team."
                ),
                "ticket_id": referenced_tid
            }

        # ----------------------------------------------------
        # 2. Confidence inquiry
        # ----------------------------------------------------
        if any(
            w in msg_lower
            for w in [
                "confidence",
                "score",
                "how sure",
                "tier"
            ]
        ):
            return {
                "reply": (
                    f"### AI Confidence Calibration for "
                    f"**{t['ticket_id']}**\n\n"

                    f"- **Confidence Score:** "
                    f"`{conf_pct}%`\n"

                    f"- **Confidence Tier:** "
                    f"`{t.get('confidence_tier', 'medium').upper()}`\n\n"

                    f"**How confidence is calculated:**\n"

                    f"The confidence score comes directly "
                    f"from the ticket classification model's "
                    f"probability for the predicted category.\n\n"

                    f"**Thresholds:**\n"
                    f"- **High:** 85% or above\n"
                    f"- **Medium:** 60% to 84.9%\n"
                    f"- **Low:** below 60%\n\n"

                    f"Historical ticket matches are shown "
                    f"separately as supporting knowledge-base evidence."
                ),
                "ticket_id": referenced_tid
            }

        # ----------------------------------------------------
        # 3. Escalation inquiry
        # ----------------------------------------------------
        if any(
            w in msg_lower
            for w in [
                "why escalated",
                "escalation",
                "escalated",
                "safety",
                "boundary"
            ]
        ):

            is_esc = (
                t.get("escalated")
                or t.get("handling_decision") == "Escalated"
            )

            if is_esc:
                return {
                    "reply": (
                        f"### Escalation Status for "
                        f"**{t['ticket_id']}**\n\n"

                        f"- **Handling:** `Escalated`\n"

                        f"- **Resolution Ownership:** "
                        f"`{t.get('resolution_ownership', 'Human Fix Required')}`\n\n"

                        f"**Reason for Escalation:**\n"

                        f"The ticket breached one of "
                        f"Resolve IQ's safety guardrails: "
                        f"either security sensitivity, "
                        f"administrative account privileges, "
                        f"or model confidence under the "
                        f"60% threshold. "

                        f"It has been designated for "
                        f"human specialist review."
                    ),
                    "ticket_id": referenced_tid
                }

            else:
                return {
                    "reply": (
                        f"### Escalation Status for "
                        f"**{t['ticket_id']}**\n\n"

                        f"- **Handling:** `Accepted`\n"

                        f"- **Resolution Ownership:** "
                        f"`{t.get('resolution_ownership', 'AI Resolution Available')}`\n\n"

                        f"This incident met the current "
                        f"confidence threshold for standard "
                        f"queue handling. Recommended actions "
                        f"remain subject to operational confirmation."
                    ),
                    "ticket_id": referenced_tid
                }

        # ----------------------------------------------------
        # 4. Resolution inquiry
        # ----------------------------------------------------
        if any(
            w in msg_lower
            for w in [
                "solution",
                "how to fix",
                "resolve",
                "resolution",
                "remediation",
                "action"
            ]
        ):

            remed_msg = (
                remed.get("message")
                or (
                    "Diagnostic guidance was prepared "
                    "based on the available ticket information."
                )
            )

            return {
                "reply": (
                    f"### Recommended Resolution for "
                    f"**{t['ticket_id']}**\n\n"

                    f"**Proposed Steps:**\n"
                    f"> {t.get('resolution', 'No automated resolution available.')}\n\n"

                    f"**Automated Diagnostic Check:**\n"

                    f"- **Diagnosis:** "
                    f"`{remed.get('diagnosis', 'Diagnostic test evaluated')}`\n"

                    f"- **Action:** "
                    f"`{remed.get('action', 'System check')}`\n"

                    f"- **Result:** {remed_msg}"
                ),
                "ticket_id": referenced_tid
            }

        # ----------------------------------------------------
        # 5. Similar tickets / RAG
        # ----------------------------------------------------
        if any(
            w in msg_lower
            for w in [
                "rag",
                "similar",
                "knowledge",
                "history",
                "previous"
            ]
        ):

            rag_list = t.get(
                "rag_results"
            ) or []

            if rag_list:

                items_text = "\n".join([
                    (
                        f"- **[{r.get('ticket_id', 'T000')}]** "
                        f"({round(float(r.get('similarity', 0)) * 100)}% match): "
                        f"{r.get('text', '')[:80]}...\n"
                        f"  *Fix:* "
                        f"{r.get('resolution', 'N/A')[:80]}"
                    )
                    for r in rag_list[:3]
                ])

                return {
                    "reply": (
                        f"### Knowledge Base Matches for "
                        f"**{t['ticket_id']}**\n\n"
                        f"{items_text}"
                    ),
                    "ticket_id": referenced_tid
                }

            else:
                return {
                    "reply": (
                        f"No similar historical ticket "
                        f"matches were recorded for "
                        f"**{t['ticket_id']}**."
                    ),
                    "ticket_id": referenced_tid
                }

        # ----------------------------------------------------
        # 6. Default ticket overview
        # ----------------------------------------------------
        return {
            "reply": (
                f"### Ticket Dossier: "
                f"**{t['ticket_id']}**\n\n"

                f"- **Subject:** {t['subject']}\n"

                f"- **Category:** `{t['category']}` "
                f"| **Priority:** `{t['priority']}`\n"

                f"- **Assigned Team:** "
                f"`{t['routing']}`\n"

                f"- **Status:** `{t['status']}`\n"

                f"- **Handling:** "
                f"`{t.get('handling_decision', 'Accepted')}` "
                f"| **Resolution:** "
                f"`{t.get('resolution_ownership', 'AI Resolution Available')}`\n"

                f"- **AI Confidence:** "
                f"`{conf_pct}%`\n\n"

                f"**Next Action:**\n"

                f"{t.get('resolution', 'Review incident details and apply recommended steps.')}"
            ),
            "ticket_id": referenced_tid
        }

    # ========================================================
    # CASE B: PLATFORM QUESTIONS & GENERAL SUPPORT
    # ========================================================

    # --------------------------------------------------------
    # Ticket submission
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "submit",
            "new ticket",
            "how to submit",
            "file",
            "upload"
        ]
    ):
        return {
            "reply": (
                "### Submitting a Support Ticket\n\n"

                "To submit a new ticket in Resolve IQ:\n"

                "1. Click **Submit Ticket** in the left sidebar "
                "or the `+ Submit New Ticket` button.\n"

                "2. Enter a subject and detailed description "
                "of the incident.\n"

                "3. Optionally select Priority or choose "
                "**Auto Detect** to let the AI infer it.\n"

                "4. Drag and drop supporting logs or screenshots "
                "(PDF, CSV, TXT, PNG, JPG).\n"

                "5. Click **Analyze Ticket** to run classification, "
                "routing, and solution generation."
            )
        }

    # --------------------------------------------------------
    # Handling / ownership
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "handling",
            "decision",
            "ownership",
            "human fix",
            "accepted"
        ]
    ):
        return {
            "reply": (
                "### Handling Decision vs. Resolution Ownership\n\n"

                "Resolve IQ clearly separates two operational concepts:\n\n"

                "1. **Handling Decision** "
                "(`Accepted` vs `Escalated`):\n"

                "   - **Accepted:** The ticket has been "
                "received and approved for regular queue handling.\n"

                "   - **Escalated:** Flagged for senior oversight "
                "or specialized Tier-2 review.\n\n"

                "2. **Resolution Ownership** "
                "(`AI Resolution Available` vs `Human Fix Required`):\n"

                "   - **AI Resolution Available:** AI-assisted "
                "resolution guidance is available for the ticket.\n"

                "   - **Human Fix Required:** Physical intervention, "
                "credential verification, or code change needed."
            )
        }

    # --------------------------------------------------------
    # Queue
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "queue",
            "bulk",
            "select all",
            "delete selected"
        ]
    ):
        return {
            "reply": (
                "### Ticket Queue & Bulk Operations\n\n"

                "The **Ticket Queue** provides complete "
                "operations management:\n"

                "- **Checkboxes & Select All:** Select multiple "
                "tickets across the queue.\n"

                "- **Bulk Actions:** Mark Selected as Resolved, "
                "Escalated, Accepted, Human Fix, or Delete Selected.\n"

                "- **Filters:** Filter in real-time by Category, "
                "Priority, Status, Escalation, or Department.\n"

                "- **Sorting:** Sort by Newest, Oldest, "
                "Priority, or Confidence."
            )
        }

    # --------------------------------------------------------
    # Clear tickets
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "clear all",
            "delete all",
            "wipe"
        ]
    ):
        return {
            "reply": (
                "### Clear All Tickets\n\n"

                "You can permanently clear all tickets by "
                "clicking the **Clear All Tickets** button "
                "on the Ticket Queue page. "

                "A confirmation modal will appear. Once confirmed, "
                "all records in SQLite are removed, KPIs reset "
                "to 0, and the queue displays an empty state."
            )
        }

    # --------------------------------------------------------
    # VPN
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "vpn",
            "cannot connect",
            "disconnect"
        ]
    ):
        return {
            "reply": (
                "### VPN Troubleshooting Steps\n\n"

                "For frequent VPN disconnects or connectivity errors:\n"

                "1. Check whether your internet connection "
                "is working normally.\n"

                "2. Restart the VPN client and try reconnecting.\n"

                "3. If the issue continues, verify the VPN settings "
                "provided by your organization.\n"

                "4. If the connection still fails, submit or "
                "escalate the ticket to Network Support."
            )
        }

    # --------------------------------------------------------
    # Password / account access
    # --------------------------------------------------------
    if any(
        w in msg_lower
        for w in [
            "password",
            "reset",
            "locked",
            "account"
        ]
    ):
        return {
            "reply": (
                "### Account Access & Password Reset Guidance\n\n"

                "1. If your organization provides a self-service "
                "password-reset portal, use the approved corporate process.\n"

                "2. If the account is locked or requires administrator "
                "verification, contact your organization's Identity "
                " & Access Management team.\n"

                "3. Password reset and account-access issues are "
                "classified under **Access Management** and routed "
                "to **Identity & Access Management**."
            )
        }

    # ========================================================
    # DEFAULT GREETING & CAPABILITIES
    # ========================================================

    return {
        "reply": (
            "👋 **Hello! I'm your Resolve IQ Support Assistant.**\n\n"

            "I can help you with:\n"

            "- **Explaining Ticket Decisions:** Ask "
            "*\"Why was TKT-XXXX classified as Network?\"* "
            "or *\"Why was this ticket escalated?\"*\n"

            "- **Confidence Insights:** Ask "
            "*\"Explain AI confidence for TKT-XXXX\"*\n"

            "- **Recommended Fixes:** Ask "
            "*\"How do I resolve TKT-XXXX?\"*\n"

            "- **Operations Help:** Inquire about bulk queue "
            "actions, handling decisions, or PDF exports.\n\n"

            "*Tip: Mention any Ticket ID "
            "(e.g. `TKT-NET-1042`) for instant contextual analysis.*"
        )
    }


@app.route("/api/chat", methods=["POST"])
def assistant_chat():
    """Chatbot endpoint for Resolve IQ floating assistant."""

    data = request.get_json(
        silent=True
    ) or {}

    message = data.get(
        "message",
        ""
    ).strip()

    ticket_id = data.get(
        "ticket_id"
    )

    if not message:
        return jsonify({
            "success": False,
            "error": "Message is required."
        }), 400

    reply_data = generate_assistant_reply(
        message,
        ticket_id
    )

    return jsonify({
        "success": True,
        **reply_data
    })


# ============================================================
# ANALYTICS API
# ============================================================

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Return aggregated live metrics and chart data."""

    summary = database.get_analytics_summary()

    return jsonify({
        "success": True,
        "analytics": summary
    })


# ============================================================
# EXPORT DATA (CSV & PDF)
# ============================================================

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Export ticket history as a downloadable CSV file."""

    search = request.args.get("search")
    category = request.args.get("category")
    priority = request.args.get("priority")
    status = request.args.get("status")
    department = request.args.get("department")
    sort_by = request.args.get("sort_by")

    tickets = database.get_all_tickets(
        search=search,
        category=category,
        priority=priority,
        status=status,
        department=department,
        sort_by=sort_by
    )

    csv_data = reports.generate_csv(
        tickets
    )

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=resolve_iq_tickets.csv"
            )
        }
    )


@app.route("/api/export/pdf", methods=["GET"])
def export_pdf():
    """
    Export ticket report as a downloadable PDF file.

    If ticket_id is supplied, return a single-ticket
    detailed dossier.

    Otherwise return an executive summary table
    of all tickets.
    """

    ticket_id = request.args.get(
        "ticket_id"
    )

    if ticket_id:

        ticket = database.get_ticket_by_id(
            ticket_id
        )

        if not ticket:
            return jsonify({
                "success": False,
                "error": (
                    f"Ticket {ticket_id} not found."
                )
            }), 404

        pdf_data = reports.generate_single_ticket_pdf(
            ticket
        )

        filename = (
            f"resolve_iq_{ticket_id}.pdf"
        )

    else:

        tickets = database.get_all_tickets()

        pdf_data = reports.generate_all_tickets_pdf(
            tickets
        )

        filename = (
            "resolve_iq_tickets_report.pdf"
        )

    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; filename={filename}"
            )
        }
    )


# ============================================================
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )