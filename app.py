"""
Resolve IQ — Command Center
----------------------------
A completely redesigned dashboard for the AI-Powered Intelligent Ticket
Routing & Resolution Agent project.

New in this version:
  - Top "pill" navigation bar (Dashboard / Submit / Queue / Analytics)
    instead of a sidebar radio menu.
  - Glassmorphism cards, animated gradient header, redesigned badges.
  - A brand-new Dashboard/home page with live KPIs + recent activity feed.
  - A Kanban-style Queue page (Needs Review / Escalated / Resolved columns)
    with search, filters, and CSV/PDF export.
  - Altair-based Analytics (donut + bar charts) instead of plain progress bars.
  - Redesigned Submit flow: tabbed result (Overview / Diagnosis / Similar
    Tickets) instead of one long scroll.

Backend logic (agent/*) is completely untouched — same imports, same
function/attribute contracts as before.
"""

import csv
import io
import os
import uuid
from datetime import datetime

import pandas as pd
import altair as alt
import streamlit as st
from fpdf import FPDF

from agent import TicketAgentPipeline, preprocessing, recurring as recurring_mod
from agent.escalation import needs_review_flag
from agent.routing import ROUTING_MAP, route
from agent.models import (
    Ticket,
    ClassificationResult,
    RoutingResult,
    ResolutionResult,
    ConfidenceResult,
    PipelineResult,
)

ALL_CATEGORIES = list(ROUTING_MAP.keys())
GENERAL_CATEGORY = "General / Other"
ATTACHMENTS_DIR = os.path.join(os.path.dirname(__file__), "attachments")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Resolve IQ — Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


# ============================================================
# PALETTES + CSS
# ============================================================

PALETTES = {
    "dark": dict(
        bg="#05060f", panel="rgba(255,255,255,0.045)", panel_solid="#0f1226",
        border="rgba(255,255,255,0.09)",
        aurora1="#22e0a3", aurora2="#7c5cff", aurora3="#ff5fa3", aurora4="#ffb020",
        text="#eef1ff", muted="#8a90b8",
        urgent="#ff4d6d", high="#ffb020", medium="#3ec6ff", low="#22e0a3",
    ),
    "light": dict(
        bg="#f3f5fb", panel="rgba(255,255,255,0.65)", panel_solid="#ffffff",
        border="rgba(20,20,50,0.08)",
        aurora1="#059669", aurora2="#7c3aed", aurora3="#db2777", aurora4="#b45309",
        text="#12142a", muted="#5b6285",
        urgent="#dc2626", high="#b45309", medium="#0891b2", low="#059669",
    ),
}

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Sora', sans-serif !important; }

#MainMenu, header[data-testid="stHeader"] { background: transparent; }

.stApp {
    background:
        radial-gradient(1200px 500px at 10% -10%, rgba(34,224,163,.16), transparent 55%),
        radial-gradient(1000px 500px at 100% 0%, rgba(124,92,255,.16), transparent 55%),
        radial-gradient(900px 600px at 50% 110%, rgba(255,95,163,.10), transparent 55%),
        var(--bg);
    color: var(--text);
}
.main .block-container { max-width: 1400px; padding-top: 1rem; padding-bottom: 4rem; }

/* ---------- HERO ---------- */
.hero-wrap {
    display:flex; align-items:center; justify-content:space-between;
    gap: 18px; flex-wrap: wrap;
    padding: 22px 26px;
    margin-bottom: 18px;
    border-radius: 22px;
    border: 1px solid var(--border);
    background: var(--panel);
    backdrop-filter: blur(14px);
}
.hero-title {
    font-size: 2.1rem; font-weight: 800; margin: 0; line-height:1.1;
    background: linear-gradient(90deg, var(--aurora1), var(--aurora2) 55%, var(--aurora3));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: var(--muted); font-weight: 500; margin-top: 4px; font-size: .95rem; }
.hero-user {
    display:flex; align-items:center; gap:10px;
    padding: 8px 16px; border-radius: 999px;
    background: var(--panel); border: 1px solid var(--border);
    font-weight: 700; font-size: .88rem;
}
.hero-avatar {
    width: 34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg, var(--aurora1), var(--aurora2));
    color: #05060f; font-weight:900;
}

/* ---------- PILL NAV ---------- */
div[data-testid="stHorizontalBlock"] .nav-pill button {
    border-radius: 999px !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: var(--panel); padding: 6px; border-radius: 999px;
    border: 1px solid var(--border); backdrop-filter: blur(10px);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important; padding: 8px 20px !important; font-weight: 700 !important;
    color: var(--muted) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--aurora1), var(--aurora2)) !important;
    color: #04060f !important;
}
.stTabs [data-baseweb="tab-highlight"] { display:none; }
.stTabs [data-baseweb="tab-border"] { display:none; }

/* ---------- GLASS CARD ---------- */
.glass {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 20px 22px;
    backdrop-filter: blur(12px);
    margin-bottom: 16px;
}
.glass-tight { padding: 14px 16px; }

/* ---------- METRICS ---------- */
[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px 18px;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-weight: 700 !important; font-size:.78rem !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 900 !important; }

/* ---------- BUTTONS ---------- */
.stButton > button {
    min-height: 44px; border-radius: 13px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); font-weight: 700;
    transition: .15s ease;
}
.stButton > button:hover { border-color: var(--aurora1); transform: translateY(-2px); }
button[kind="primary"], .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--aurora1), var(--aurora2)) !important;
    color: #04060f !important; border: none !important;
    box-shadow: 0 10px 26px rgba(124,92,255,.28);
}
.stDownloadButton > button {
    min-height: 44px; border-radius: 13px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); font-weight: 700;
}

/* ---------- INPUTS ---------- */
.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: var(--panel-solid) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 13px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--aurora1) !important; box-shadow: 0 0 0 3px rgba(34,224,163,.16) !important;
}

/* ---------- FILE UPLOADER ---------- */
[data-testid="stFileUploader"] section {
    background: var(--panel) !important; border: 1px dashed var(--border) !important; border-radius: 14px !important;
}

/* ---------- EXPANDER ---------- */
.streamlit-expanderHeader {
    background: var(--panel) !important; border-radius: 12px !important; font-weight: 700 !important;
    border: 1px solid var(--border) !important; color: var(--text) !important;
}

/* ---------- BADGES ---------- */
.badge {
    display:inline-block; padding: 5px 13px; border-radius: 999px; font-weight: 800;
    font-size: .74rem; letter-spacing:.3px; margin-right:6px; margin-bottom:4px;
}
.badge-high     { background: rgba(34,224,163,.16); color: var(--low); border:1px solid var(--low); }
.badge-medium   { background: rgba(62,198,255,.16); color: var(--medium); border:1px solid var(--medium); }
.badge-low      { background: rgba(255,77,109,.16); color: var(--urgent); border:1px solid var(--urgent); }
.badge-internal { background: rgba(34,224,163,.16); color: var(--low); border:1px solid var(--low); }
.badge-external { background: rgba(255,176,32,.16); color: var(--high); border:1px solid var(--high); }
.badge-human    { background: rgba(124,92,255,.18); color: var(--aurora2); border:1px solid var(--aurora2); }
.badge-p-urgent { background: rgba(255,77,109,.2); color: var(--urgent); border:1px solid var(--urgent); }
.badge-p-high   { background: rgba(255,176,32,.2); color: var(--high); border:1px solid var(--high); }
.badge-p-medium { background: rgba(62,198,255,.18); color: var(--medium); border:1px solid var(--medium); }
.badge-p-low    { background: rgba(34,224,163,.18); color: var(--low); border:1px solid var(--low); }

/* ---------- KANBAN ---------- */
.kanban-col-head {
    font-weight: 800; font-size: .95rem; padding: 6px 2px 10px 2px;
    display:flex; align-items:center; justify-content:space-between;
    border-bottom: 1px solid var(--border); margin-bottom: 10px;
}
.ticket-card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
    padding: 14px 16px; margin-bottom: 12px;
}
.ticket-card:hover { border-color: var(--aurora1); }
.ticket-id { font-family: monospace; color: var(--muted); font-size: .75rem; }
.ticket-text { font-size: .88rem; margin: 6px 0 8px 0; color: var(--text); }

/* ---------- FOOTER ---------- */
.footer { text-align:center; padding: 26px 0 8px 0; color: var(--muted); border-top: 1px solid var(--border); margin-top: 30px; }

/* ---------- MOBILE ---------- */
@media (max-width: 680px) {
    .main .block-container { padding-left:.6rem; padding-right:.6rem; }
    .hero-title { font-size: 1.5rem; }
    .hero-wrap { padding: 16px 16px; }
    [data-testid="stMetricValue"] { font-size: 1.05rem !important; }
    .stTabs [data-baseweb="tab"] { padding: 7px 12px !important; font-size:.8rem !important; }
}
"""


def inject_css(theme: str):
    p = PALETTES[theme]
    root_vars = f"""
    :root {{
        --bg: {p['bg']}; --panel: {p['panel']}; --panel-solid: {p['panel_solid']}; --border: {p['border']};
        --aurora1: {p['aurora1']}; --aurora2: {p['aurora2']}; --aurora3: {p['aurora3']}; --aurora4: {p['aurora4']};
        --text: {p['text']}; --muted: {p['muted']};
        --urgent: {p['urgent']}; --high: {p['high']}; --medium: {p['medium']}; --low: {p['low']};
    }}
    """
    st.markdown(f"<style>{root_vars}{BASE_CSS}</style>", unsafe_allow_html=True)


inject_css(st.session_state.theme)


# ============================================================
# HELPERS: badges, priority, scope
# ============================================================

def tier_badge(tier: str) -> str:
    tier = (tier or "").lower()
    cls = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(tier, "badge-medium")
    return f'<span class="badge {cls}">{tier.upper()} CONFIDENCE</span>'


def priority_badge(priority: str) -> str:
    cls = {
        "Urgent": "badge-p-urgent", "High": "badge-p-high",
        "Medium": "badge-p-medium", "Low": "badge-p-low",
    }.get(priority, "badge-p-medium")
    return f'<span class="badge {cls}">PRIORITY: {priority.upper()}</span>'


def scope_badge(scope: str) -> str:
    cls = {"internal": "badge-internal", "external": "badge-external", "needs_human": "badge-human"}[scope]
    label = {"internal": "FIXED INTERNALLY", "external": "NEEDS EXTERNAL ACTION", "needs_human": "NEEDS A HUMAN AGENT"}[scope]
    return f'<span class="badge {cls}">{label}</span>'


EXTERNAL_CATEGORIES = {"Security", "Access Management", "Database"}
URGENT_KEYWORDS = ["urgent", "asap", "emergency", "critical", "immediately", "production down", "outage"]


def diagnose_scope(category: str, remediation: dict) -> str:
    if category in EXTERNAL_CATEGORIES:
        return "external"
    if remediation.get("success"):
        return "internal"
    return "needs_human"


def estimate_priority(text: str, category: str, confidence_tier: str, escalated: bool) -> str:
    text_l = (text or "").lower()
    if any(k in text_l for k in URGENT_KEYWORDS):
        return "Urgent"
    if category == "Security":
        return "Urgent" if escalated else "High"
    if escalated or confidence_tier == "low":
        return "High"
    if confidence_tier == "medium":
        return "Medium"
    return "Low"


def guidance_lines(remediation: dict, scope: str):
    diagnosis = remediation.get("diagnosis", "No diagnosis available.")
    action = remediation.get("action", "No action taken.")
    message = remediation.get("message", "")

    if scope == "internal":
        return [
            f"**Diagnosis:** {diagnosis}",
            f"**Action taken automatically:** {action}",
            message,
            "✅ No further action needed from you — the agent handled this safely on its own.",
        ]
    if scope == "external":
        return [
            f"**Diagnosis:** {diagnosis}",
            message,
            "🚫 This category (credentials, accounts, security or database access) is "
            "intentionally **never modified automatically** — that's a safety boundary, not a bug.",
            "**What to do:** contact the department shown above directly, or use your "
            "organization's normal process for this kind of request.",
        ]
    return [
        f"**Diagnosis:** {diagnosis}",
        f"**Attempted action:** {action}",
        message,
        "👤 The AI identified the problem and tried a safe check, but couldn't fully resolve it. "
        "**A human support agent should pick this up from here.**",
    ]


def ticket_status(result) -> str:
    """Derives a Kanban status from what we already track."""
    tid = result.ticket.id
    if tid in st.session_state.escalated_by_agent:
        return "Escalated"
    if tid in st.session_state.accepted:
        return "Resolved"
    if result.escalated:
        return "Needs Review"
    return "Needs Review" if needs_review_flag(result.confidence) else "Resolved"


# ============================================================
# SESSION STATE
# ============================================================

for key, default in [
    ("history", []), ("accepted", set()), ("escalated_by_agent", set()),
    ("example_ticket", ""), ("username", ""), ("logged_in", False),
    ("user_id", ""), ("user_org", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


# ============================================================
# LOGIN
# ============================================================

def page_login():
    st.markdown(
        """
        <div style="text-align:center; margin-top: 9vh;">
            <div style="font-size:3.2rem;">🛰️</div>
            <div style="font-size:2.6rem; font-weight:800; font-family:'Sora', sans-serif;
                        background: linear-gradient(90deg, var(--aurora1), var(--aurora2), var(--aurora3));
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                        letter-spacing: -1px;">
                Resolve IQ
            </div>
            <div style="color:var(--muted); font-size:1.05rem; margin-top:4px;">
                Command Center for AI-powered ticket routing &amp; resolution
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown('<div class="glass" style="margin-top:24px;">', unsafe_allow_html=True)
        st.markdown("#### 👋 Sign in to continue")
        name = st.text_input("Your name", placeholder="e.g. Priya Sharma")
        user_id = st.text_input("Employee / Student ID", placeholder="e.g. EMP1042")
        org = st.text_input("Organization name", placeholder="e.g. Acme Corp")

        if st.button("🚀 Enter Command Center", use_container_width=True, type="primary"):
            if name.strip():
                st.session_state.logged_in = True
                st.session_state.username = name.strip()
                st.session_state.user_id = user_id.strip()
                st.session_state.user_org = org.strip()
                st.rerun()
            else:
                st.warning("Please enter your name at least.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="position: fixed; bottom: 14px; right: 22px; color: var(--muted);
                    font-size: 0.85rem; font-weight: 600;">
            Made by Akriti Biswas and Siddhi Kale
        </div>
        """,
        unsafe_allow_html=True,
    )


if not st.session_state.logged_in:
    page_login()
    st.stop()


@st.cache_resource
def get_pipeline():
    return TicketAgentPipeline()


pipeline = get_pipeline()


# ============================================================
# HERO HEADER + TOP CONTROLS (replaces sidebar nav)
# ============================================================

initials = "".join([w[0] for w in st.session_state.username.split()[:2]]).upper() or "?"

hc1, hc2 = st.columns([3, 1.1])
with hc1:
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div>
                <div class="hero-title">🛰️ Resolve IQ</div>
                <div class="hero-sub">Classification • RAG Retrieval • Confidence • Remediation • Escalation</div>
            </div>
            <div class="hero-user">
                <div class="hero-avatar">{initials}</div>
                <div>
                    {st.session_state.username}
                    {f"<br><span style='color:var(--muted); font-weight:500;'>{st.session_state.user_org}</span>" if st.session_state.user_org else ""}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    st.write("")
    b1, b2, b3 = st.columns(3)
    with b1:
        theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
        if st.button(theme_icon, use_container_width=True, help="Toggle theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with b2:
        if st.button("🗑️", use_container_width=True, help="Clear session"):
            st.session_state.history = []
            st.session_state.accepted = set()
            st.session_state.escalated_by_agent = set()
            st.session_state.example_ticket = ""
            st.rerun()
    with b3:
        if st.button("🔓", use_container_width=True, help="Log out"):
            st.session_state.logged_in = False
            st.rerun()

tab_dash, tab_submit, tab_queue, tab_analytics = st.tabs(
    ["🏠  Dashboard", "🎫  Submit", "🗂️  Queue", "📊  Analytics"]
)

EXAMPLES = [
    ("📶 VPN down", "I cannot connect to the company VPN from home."),
    ("💥 App crashing", "The CRM application crashes every time I open it."),
    ("🔑 Locked out", "I forgot my password and I'm locked out of my account."),
    ("🛑 Phishing email", "I received a suspicious email asking for my login details."),
    ("🗄️ DB slow", "Our database queries have suddenly become very slow."),
    ("💾 Storage full", "My cloud storage quota is full and uploads are failing."),
    ("🖥️ Server down", "The production server is unresponsive and services are down."),
]


# ============================================================
# GENERAL / OTHER QUERY PATH
# ============================================================

def build_general_query_result(raw_text: str, user: str = None) -> PipelineResult:
    ticket = Ticket(id=str(uuid.uuid4())[:8], text=raw_text, submitted_at=datetime.utcnow(), user=user)
    clean_text = preprocessing.preprocess(raw_text)

    retrieved = pipeline.retriever.search(clean_text, top_k=3)
    recurring_flag = recurring_mod.detect(retrieved)

    classification_result = ClassificationResult(category=GENERAL_CATEGORY, confidence=0.0)
    routing_result = RoutingResult(department="General / Human Review")
    resolution_result = ResolutionResult(
        suggested_steps="This wasn't matched against a known IT category — a human should read it directly."
    )
    confidence_result = ConfidenceResult(score=0.0, tier="low")
    remediation = {
        "diagnosis": "Not a recognized IT support category.",
        "action": "No automated action attempted.",
        "success": False,
        "message": (
            "Submitted as a General / Other query, so it was intentionally not forced "
            "into an IT category. Routed straight to a human for review."
        ),
    }

    return PipelineResult(
        ticket=ticket, classification=classification_result, routing=routing_result,
        retrieved=retrieved, resolution=resolution_result, confidence=confidence_result,
        recurring=recurring_flag, escalated=True, remediation=remediation,
    )


# ============================================================
# EXPORT HELPERS
# ============================================================

def history_to_rows(history):
    rows = []
    for r in history:
        rows.append({
            "ticket_id": r.ticket.id,
            "user": r.ticket.user or "",
            "submitted_at": r.ticket.submitted_at.strftime("%Y-%m-%d %H:%M"),
            "text": r.ticket.text,
            "category": r.classification.category,
            "department": r.routing.department,
            "confidence": f"{r.confidence.score:.0%}",
            "tier": r.confidence.tier,
            "priority": getattr(r, "priority", "Medium"),
            "status": ticket_status(r),
            "escalated": "Yes" if r.escalated else "No",
            "recurring": "Yes" if r.recurring.is_recurring else "No",
        })
    return rows


def rows_to_csv_bytes(rows) -> bytes:
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def rows_to_pdf_bytes(rows) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Resolve IQ - Ticket Report")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  |  {len(rows)} ticket(s)")
    pdf.ln(8)

    headers = ["ticket_id", "category", "department", "priority", "status", "tier", "escalated", "recurring", "text"]
    widths = [16, 24, 30, 15, 20, 14, 14, 14, 100]

    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h.upper(), border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7.5)
    for row in rows:
        for h, w in zip(headers, widths):
            value = str(row.get(h, ""))[:80]
            pdf.cell(w, 6, value, border=1)
        pdf.ln()

    return bytes(pdf.output())


def render_export_buttons(rows, key_prefix):
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "⬇️ Export CSV", data=rows_to_csv_bytes(rows),
            file_name="tickets_export.csv", mime="text/csv",
            use_container_width=True, key=f"{key_prefix}_csv", disabled=not rows,
        )
    with e2:
        st.download_button(
            "⬇️ Export PDF", data=rows_to_pdf_bytes(rows) if rows else b"",
            file_name="tickets_export.pdf", mime="application/pdf",
            use_container_width=True, key=f"{key_prefix}_pdf", disabled=not rows,
        )


# ============================================================
# TAB: DASHBOARD (new)
# ============================================================

with tab_dash:
    history = st.session_state.history

    total = len(history)
    escalated = sum(1 for r in history if r.escalated)
    recurring = sum(1 for r in history if r.recurring.is_recurring)
    avg_conf = (sum(r.confidence.score for r in history) / total) if total else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🎫 Total Tickets", total)
    k2.metric("🚨 Escalated", escalated)
    k3.metric("🔁 Recurring", recurring)
    k4.metric("🎯 Avg Confidence", f"{avg_conf:.0%}")

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown('<div class="glass"><h4>🕒 Recent Activity</h4>', unsafe_allow_html=True)
        if not history:
            st.info("No tickets yet — head to **Submit** to analyze your first one.")
        else:
            for r in history[:6]:
                status = ticket_status(r)
                st.markdown(
                    f"""
                    <div class="ticket-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="ticket-id">#{r.ticket.id}</span>
                            <span>{priority_badge(getattr(r, "priority", "Medium"))}</span>
                        </div>
                        <div class="ticket-text">{(r.ticket.text[:110] + "…") if len(r.ticket.text) > 110 else r.ticket.text}</div>
                        <div>{tier_badge(r.confidence.tier)} <span class="badge badge-human">{status.upper()}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass"><h4>⚡ Quick Submit</h4>', unsafe_allow_html=True)
        st.caption("Jump-start a ticket with a one-tap example, then fine-tune it in Submit.")
        for label, text in EXAMPLES[:5]:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state.example_ticket = text
                st.info("Loaded into the Submit tab — click 🎫 Submit above.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass"><h4>🛠️ Resolution Mix</h4>', unsafe_allow_html=True)
        if history:
            scopes = {"internal": 0, "external": 0, "needs_human": 0}
            for r in history:
                scopes[diagnose_scope(r.classification.category, r.remediation)] += 1
            st.write(f"🤖 Fixed internally: **{scopes['internal']}**")
            st.write(f"🚫 Needs external action: **{scopes['external']}**")
            st.write(f"👤 Needs a human: **{scopes['needs_human']}**")
        else:
            st.caption("Nothing processed yet.")
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TAB: SUBMIT
# ============================================================

with tab_submit:
    st.markdown("### 🔄 Submit a new ticket")

    mode = st.radio(
        "What kind of thing are you submitting?",
        ["🎫 IT Support Ticket", "🧭 General / Other Query"],
        horizontal=True,
        help="Use General/Other for anything that isn't a standard IT ticket — "
             "it skips forced auto-classification and goes straight to a human.",
    )

    st.markdown("###### Quick-fill examples")
    cols = st.columns(4)
    for i, (label, text) in enumerate(EXAMPLES):
        with cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"example_{i}"):
                st.session_state.example_ticket = text

    ticket_text = st.text_area(
        "Describe the issue",
        value=st.session_state.example_ticket,
        height=130,
        placeholder="e.g. My laptop won't connect to the office Wi-Fi...",
    )

    uploaded_file = st.file_uploader("📎 Attach a file (optional) — screenshot, log, etc.")

    submitted = st.button("🚀 Analyze Ticket", use_container_width=True, type="primary")

    if submitted and ticket_text.strip():
        user = st.session_state.username.strip() or None

        if mode.startswith("🎫"):
            with st.spinner("🤖 Classifying, routing, retrieving similar tickets, checking confidence..."):
                result = pipeline.run(
                    ticket_id=str(uuid.uuid4())[:8],
                    raw_text=ticket_text.strip(),
                    user=user,
                )
        else:
            with st.spinner("🧭 Searching for anything similar, then routing straight to a human..."):
                result = build_general_query_result(ticket_text.strip(), user=user)

        result.priority = estimate_priority(
            ticket_text, result.classification.category, result.confidence.tier, result.escalated
        )

        result.attachment = None
        if uploaded_file is not None:
            safe_name = f"{result.ticket.id}_{uploaded_file.name}"
            save_path = os.path.join(ATTACHMENTS_DIR, safe_name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            result.attachment = {"name": uploaded_file.name, "size": uploaded_file.size, "path": save_path}

        st.session_state.history.insert(0, result)
        st.session_state.example_ticket = ticket_text.strip()
    elif submitted:
        st.warning("Please describe the issue before submitting.")

    if st.session_state.history:
        result = st.session_state.history[0]

        st.markdown("---")
        st.markdown("### 🎯 Result")

        c1, c2, c3 = st.columns(3)
        c1.metric("Category", result.classification.category)
        c2.metric("Department", result.routing.department)
        c3.metric("AI Confidence", f"{result.confidence.score:.0%}")

        st.markdown(
            tier_badge(result.confidence.tier) + priority_badge(getattr(result, "priority", "Medium")),
            unsafe_allow_html=True,
        )

        if getattr(result, "attachment", None):
            st.caption(f"📎 Attached: {result.attachment['name']} ({result.attachment['size']} bytes)")

        if result.escalated:
            st.error("🚨 **LOW CONFIDENCE** — this ticket has been escalated for human expert review.")
        elif needs_review_flag(result.confidence):
            st.warning("⚠️ **MEDIUM CONFIDENCE** — recommendation shown, but flagged for agent review before acting.")
        else:
            st.success("✅ **HIGH CONFIDENCE** — the AI recommendation can be actioned directly.")

        with st.expander("✏️ Not right? Manually fix the category / department"):
            override_options = ALL_CATEGORIES + [GENERAL_CATEGORY]
            current = result.classification.category
            default_index = override_options.index(current) if current in override_options else len(override_options) - 1

            new_category = st.selectbox(
                "Correct category", override_options, index=default_index,
                key=f"override_select_{result.ticket.id}",
            )

            if st.button("Apply override", key=f"override_apply_{result.ticket.id}"):
                result.classification.category = new_category
                if new_category == GENERAL_CATEGORY:
                    result.routing.department = "General / Human Review"
                    result.escalated = True
                else:
                    result.routing.department = route(new_category).department
                result.remediation["message"] = (
                    result.remediation.get("message", "")
                    + " (Category manually corrected by an agent — automated diagnosis above may no longer apply.)"
                ).strip()
                result.priority = estimate_priority(
                    result.ticket.text, new_category, result.confidence.tier, result.escalated
                )
                st.success(f"Category corrected to **{new_category}**.")
                st.rerun()

        result_tab1, result_tab2, result_tab3 = st.tabs(["💡 Resolution", "🛠️ Diagnosis & Fix", "📚 Similar Tickets"])

        with result_tab1:
            st.info(result.resolution.suggested_steps)
            if result.recurring.is_recurring:
                st.warning(f"🔁 **Recurring issue detected** — {result.recurring.cluster_size} related tickets found in history.")
            else:
                st.success("🔹 No significant recurring pattern detected.")

        with result_tab2:
            remediation = result.remediation
            scope = diagnose_scope(result.classification.category, remediation)
            st.markdown(scope_badge(scope), unsafe_allow_html=True)
            st.markdown('<div class="glass glass-tight">', unsafe_allow_html=True)
            for line in guidance_lines(remediation, scope):
                if line:
                    st.markdown(line)
            st.markdown("</div>", unsafe_allow_html=True)

        with result_tab3:
            if result.retrieved:
                for t in result.retrieved:
                    st.markdown(f"**{t.ticket_id}** — similarity {t.similarity:.0%}")
                    st.caption(t.text)
                    if t.resolution:
                        st.write(f"Resolution: {t.resolution}")
                    st.markdown("---")
            else:
                st.caption("No similar historical tickets found.")


# ============================================================
# TAB: QUEUE (Kanban-style, replaces plain History list)
# ============================================================

with tab_queue:
    history = st.session_state.history

    if not history:
        st.info("No tickets processed yet. Go to **Submit** to analyze your first one.")
    else:
        st.markdown("#### 🔍 Search & Filter")
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            search_query = st.text_input("Search ticket text", placeholder="e.g. VPN, password, crash...")
        with f2:
            available_categories = sorted({r.classification.category for r in history})
            selected_categories = st.multiselect("Category", available_categories)
        with f3:
            selected_priorities = st.multiselect("Priority", ["Urgent", "High", "Medium", "Low"])

        filtered = history
        if search_query:
            filtered = [r for r in filtered if search_query.lower() in r.ticket.text.lower()]
        if selected_categories:
            filtered = [r for r in filtered if r.classification.category in selected_categories]
        if selected_priorities:
            filtered = [r for r in filtered if getattr(r, "priority", "Medium") in selected_priorities]

        st.caption(f"Showing {len(filtered)} of {len(history)} ticket(s).")
        render_export_buttons(history_to_rows(filtered), key_prefix="queue")
        st.markdown("---")

        columns_def = [
            ("Needs Review", "⏳"),
            ("Escalated", "🚨"),
            ("Resolved", "✅"),
        ]
        kcols = st.columns(3)

        for (status_name, icon), kcol in zip(columns_def, kcols):
            bucket = [r for r in filtered if ticket_status(r) == status_name]
            with kcol:
                st.markdown(
                    f'<div class="kanban-col-head"><span>{icon} {status_name}</span>'
                    f'<span class="badge badge-human">{len(bucket)}</span></div>',
                    unsafe_allow_html=True,
                )
                for result in bucket:
                    ticket_id = result.ticket.id
                    priority = getattr(result, "priority", "Medium")
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <span class="ticket-id">#{ticket_id}</span>
                                    <span class="badge badge-human">{result.classification.category}</span>
                                </div>
                                <div class="ticket-text">{result.ticket.text}</div>
                                <div>{priority_badge(priority)} {tier_badge(result.confidence.tier)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        with st.expander("Details & actions"):
                            if result.ticket.user:
                                st.caption(f"👤 Submitted by: {result.ticket.user}")
                            if getattr(result, "attachment", None):
                                st.caption(f"📎 Attached: {result.attachment['name']}")

                            remediation = result.remediation
                            scope = diagnose_scope(result.classification.category, remediation)
                            st.markdown(scope_badge(scope), unsafe_allow_html=True)
                            st.caption(remediation.get("message", ""))

                            if result.recurring.is_recurring:
                                st.warning(f"🔁 Recurring — {result.recurring.cluster_size} related tickets")

                            a1, a2 = st.columns(2)
                            with a1:
                                if st.button("✅ Accept", key=f"accept_{ticket_id}", use_container_width=True):
                                    st.session_state.accepted.add(ticket_id)
                                    st.session_state.escalated_by_agent.discard(ticket_id)
                                    st.rerun()
                            with a2:
                                if st.button("🚨 Escalate", key=f"escalate_{ticket_id}", use_container_width=True):
                                    st.session_state.escalated_by_agent.add(ticket_id)
                                    st.session_state.accepted.discard(ticket_id)
                                    st.rerun()

                            st.text_area("Investigation notes", key=f"notes_{ticket_id}", height=70)


# ============================================================
# TAB: ANALYTICS (Altair charts, replaces progress-bar list)
# ============================================================

with tab_analytics:
    history = st.session_state.history

    if not history:
        st.info("No data yet. Process some tickets first from **Submit**.")
    else:
        avg_confidence = sum(r.confidence.score for r in history) / len(history)
        recurring_count = sum(1 for r in history if r.recurring.is_recurring)
        accepted_count = len(st.session_state.accepted)
        agent_escalations = len(st.session_state.escalated_by_agent)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🎯 Avg Confidence", f"{avg_confidence:.0%}")
        k2.metric("🔁 Recurring Candidates", recurring_count)
        k3.metric("✅ Accepted", accepted_count)
        k4.metric("👨‍💻 Agent Escalations", agent_escalations)

        chart_colors = ["#22e0a3", "#7c5cff", "#ff5fa3", "#ffb020", "#3ec6ff", "#ff4d6d", "#38bdf8"]

        colA, colB = st.columns(2)

        with colA:
            st.markdown('<div class="glass"><h4>🗂️ Tickets by Category</h4>', unsafe_allow_html=True)
            cat_df = pd.DataFrame(
                [{"category": r.classification.category} for r in history]
            ).value_counts("category").reset_index(name="count")
            chart = (
                alt.Chart(cat_df)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("count:Q", title="Tickets"),
                    y=alt.Y("category:N", sort="-x", title=""),
                    color=alt.Color("category:N", scale=alt.Scale(range=chart_colors), legend=None),
                    tooltip=["category", "count"],
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with colB:
            st.markdown('<div class="glass"><h4>🎯 Confidence Tier Mix</h4>', unsafe_allow_html=True)
            tier_df = pd.DataFrame(
                [{"tier": r.confidence.tier.title()} for r in history]
            ).value_counts("tier").reset_index(name="count")
            donut = (
                alt.Chart(tier_df)
                .mark_arc(innerRadius=60)
                .encode(
                    theta="count:Q",
                    color=alt.Color("tier:N", scale=alt.Scale(
                        domain=["High", "Medium", "Low"],
                        range=["#22e0a3", "#3ec6ff", "#ff4d6d"],
                    )),
                    tooltip=["tier", "count"],
                )
                .properties(height=280)
            )
            st.altair_chart(donut, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        colC, colD = st.columns(2)

        with colC:
            st.markdown('<div class="glass"><h4>🚦 Tickets by Priority</h4>', unsafe_allow_html=True)
            priority_order = ["Urgent", "High", "Medium", "Low"]
            prio_df = pd.DataFrame(
                [{"priority": getattr(r, "priority", "Medium")} for r in history]
            ).value_counts("priority").reindex(priority_order, fill_value=0).reset_index()
            prio_df.columns = ["priority", "count"]
            prio_chart = (
                alt.Chart(prio_df)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("priority:N", sort=priority_order, title=""),
                    y=alt.Y("count:Q", title="Tickets"),
                    color=alt.Color("priority:N", scale=alt.Scale(
                        domain=priority_order,
                        range=["#ff4d6d", "#ffb020", "#3ec6ff", "#22e0a3"],
                    ), legend=None),
                    tooltip=["priority", "count"],
                )
                .properties(height=260)
            )
            st.altair_chart(prio_chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with colD:
            st.markdown('<div class="glass"><h4>🛠️ Internal vs External vs Human</h4>', unsafe_allow_html=True)
            scopes = {"internal": 0, "external": 0, "needs_human": 0}
            for result in history:
                scopes[diagnose_scope(result.classification.category, result.remediation)] += 1
            scope_df = pd.DataFrame([
                {"scope": "Fixed Internally", "count": scopes["internal"]},
                {"scope": "Needs External Action", "count": scopes["external"]},
                {"scope": "Needs a Human", "count": scopes["needs_human"]},
            ])
            scope_chart = (
                alt.Chart(scope_df)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("count:Q", title="Tickets"),
                    y=alt.Y("scope:N", sort="-x", title=""),
                    color=alt.Color("scope:N", scale=alt.Scale(
                        range=["#22e0a3", "#ffb020", "#7c5cff"]
                    ), legend=None),
                    tooltip=["scope", "count"],
                )
                .properties(height=260)
            )
            st.altair_chart(scope_chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass"><h4>🏢 Tickets by Department</h4>', unsafe_allow_html=True)
        routing_counts = {}
        for result in history:
            routing_counts[result.routing.department] = routing_counts.get(result.routing.department, 0) + 1
        for department, count in sorted(routing_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{department}** — {count} ticket(s)")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("#### 📤 Export Everything")
        render_export_buttons(history_to_rows(history), key_prefix="analytics")


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="footer">
    <div style="font-size:1.05rem; font-weight:800; color:var(--text);">
        Resolve IQ — AI-Powered Intelligent Ticket Routing &amp; Resolution Agent
    </div>
    <div style="margin-top:8px;">
        Classification • RAG • Resolution • Remediation • Escalation
    </div>
    <div style="margin-top:12px;">
        Made by Akriti Biswas and Siddhi Kale
    </div>
</div>
""",
    unsafe_allow_html=True,
)