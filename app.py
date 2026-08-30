"""
AI-Powered Intelligent Ticket Routing & Resolution Agent
---------------------------------------------------------
Colorful dashboard (dark/light) with sidebar navigation
(Submit / History / Analytics), search & filtering, CSV/PDF
export, priority estimation, file attachments, a lightweight
username field, and mobile-responsive layout.

Backend logic (agent/*) is untouched.
"""

import csv
import io
import os
import uuid
from datetime import datetime

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
# PAGE CONFIG (must be the first Streamlit call)
# ============================================================

st.set_page_config(
    page_title="Resolve IQ",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme must be known BEFORE we build the CSS block below.
if "theme" not in st.session_state:
    st.session_state.theme = "dark"


# ============================================================
# COLOR PALETTES + CSS (dark / light, mobile-responsive)
# ============================================================

PALETTES = {
    "dark": dict(
        bg="#0a0b16", panel="#12142a", panel2="#171a35",
        cyan="#00e5ff", magenta="#ff3fa4", purple="#8b5cf6",
        gold="#ffb020", green="#22e0a3", red="#ff4d6d",
        text="#f2f4ff", muted="#9aa3c7",
    ),
    "light": dict(
        bg="#f4f6fb", panel="#ffffff", panel2="#eef1fb",
        cyan="#0891b2", magenta="#db2777", purple="#7c3aed",
        gold="#b45309", green="#059669", red="#dc2626",
        text="#12142a", muted="#5b6285",
    ),
}

STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;900&family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; }

.stApp {
    background:
        radial-gradient(circle at 8% 8%, rgba(0, 229, 255, .14), transparent 30%),
        radial-gradient(circle at 92% 12%, rgba(255, 63, 164, .12), transparent 32%),
        radial-gradient(circle at 50% 100%, rgba(139, 92, 246, .12), transparent 36%),
        var(--bg);
    color: var(--text);
}

.main .block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 4rem; }

/* ---------- SIDEBAR ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--panel-2) 0%, var(--panel) 100%);
    border-right: 1px solid rgba(139, 92, 246, .25);
}
[data-testid="stSidebar"] * { color: var(--text); }

[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: linear-gradient(135deg, var(--panel-2), var(--panel));
    border: 1px solid rgba(139, 92, 246, .3);
    border-radius: 14px;
    padding: 12px 14px !important;
    margin-bottom: 10px;
    width: 100%;
    transition: .18s ease;
    font-weight: 700;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    border-color: var(--cyan);
    transform: translateX(4px);
    box-shadow: 0 6px 18px rgba(0, 229, 255, .18);
}

/* ---------- HEADINGS ---------- */
h1 {
    font-size: 2.7rem !important;
    font-weight: 900 !important;
    background: linear-gradient(90deg, var(--cyan), var(--magenta), var(--gold));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px !important;
}
h2 { font-weight: 800 !important; color: var(--text) !important; }
h3 { font-weight: 800 !important; color: var(--text) !important; }

/* ---------- METRICS ---------- */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, var(--panel-2), var(--panel));
    border: 1px solid rgba(139, 92, 246, .3);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 14px 34px rgba(0, 0, 0, .18);
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-weight: 700 !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 900 !important; }

/* ---------- BUTTONS ---------- */
.stButton > button {
    min-height: 46px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, var(--cyan), var(--purple));
    color: #04060f;
    font-weight: 800;
    transition: .18s ease;
    box-shadow: 0 8px 22px rgba(139, 92, 246, .22);
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.01);
    box-shadow: 0 14px 30px rgba(0, 229, 255, .3);
    filter: brightness(1.08);
}
.stButton > button:active { transform: translateY(0); }

.stDownloadButton > button {
    min-height: 46px;
    border-radius: 14px;
    border: 1px solid rgba(139, 92, 246, .4);
    background: var(--panel-2);
    color: var(--text);
    font-weight: 800;
}

/* ---------- INPUTS ---------- */
.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div, .stDateInput input {
    background: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid rgba(139, 92, 246, .35) !important;
    border-radius: 14px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px rgba(0, 229, 255, .18) !important;
}

/* ---------- EXPANDER ---------- */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, var(--panel-2), var(--panel)) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: 1px solid rgba(139, 92, 246, .25) !important;
    color: var(--text) !important;
}

/* ---------- ALERTS ---------- */
div[data-testid="stAlert"] { border-radius: 14px !important; }

/* ---------- FILE UPLOADER ---------- */
[data-testid="stFileUploader"] section {
    background: var(--panel) !important;
    border: 1px dashed rgba(139, 92, 246, .4) !important;
    border-radius: 14px !important;
}

/* ---------- BADGE PILLS ---------- */
.badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-weight: 800;
    font-size: .8rem;
    letter-spacing: .3px;
    margin-right: 6px;
    margin-bottom: 4px;
}
.badge-high      { background: rgba(34, 224, 163, .18); color: var(--green); border: 1px solid var(--green); }
.badge-medium    { background: rgba(255, 176, 32, .18); color: var(--gold); border: 1px solid var(--gold); }
.badge-low       { background: rgba(255, 77, 109, .18); color: var(--red); border: 1px solid var(--red); }
.badge-internal  { background: rgba(0, 229, 255, .18); color: var(--cyan); border: 1px solid var(--cyan); }
.badge-external  { background: rgba(255, 63, 164, .18); color: var(--magenta); border: 1px solid var(--magenta); }
.badge-human     { background: rgba(139, 92, 246, .2); color: var(--purple); border: 1px solid var(--purple); }
.badge-p-urgent  { background: rgba(255, 77, 109, .22); color: var(--red); border: 1px solid var(--red); }
.badge-p-high    { background: rgba(255, 176, 32, .22); color: var(--gold); border: 1px solid var(--gold); }
.badge-p-medium  { background: rgba(0, 229, 255, .18); color: var(--cyan); border: 1px solid var(--cyan); }
.badge-p-low     { background: rgba(34, 224, 163, .18); color: var(--green); border: 1px solid var(--green); }

.glow-card {
    background: linear-gradient(145deg, var(--panel-2), var(--panel));
    border: 1px solid rgba(139, 92, 246, .3);
    border-radius: 18px;
    padding: 20px 22px;
    margin-bottom: 14px;
}
.footer {
    text-align: center;
    padding: 26px 0 8px 0;
    color: var(--muted);
    border-top: 1px solid rgba(139, 92, 246, .2);
    margin-top: 30px;
}

/* ---------- MOBILE RESPONSIVENESS ---------- */
@media (max-width: 680px) {
    .main .block-container { padding-left: 0.7rem; padding-right: 0.7rem; padding-top: 0.8rem; }
    h1 { font-size: 1.7rem !important; letter-spacing: -0.5px !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.05rem !important; }
    [data-testid="stMetric"] { padding: 12px 14px; }
    [data-testid="stMetricValue"] { font-size: 1.15rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
    .stButton > button { font-size: 0.82rem; padding: 10px 8px; min-height: 42px; }
    .badge { font-size: .68rem; padding: 4px 10px; }
    .glow-card { padding: 14px 16px; }
}
"""


def inject_css(theme: str):
    p = PALETTES[theme]
    root_vars = f"""
    :root {{
        --bg: {p['bg']};
        --panel: {p['panel']};
        --panel-2: {p['panel2']};
        --cyan: {p['cyan']};
        --magenta: {p['magenta']};
        --purple: {p['purple']};
        --gold: {p['gold']};
        --green: {p['green']};
        --red: {p['red']};
        --text: {p['text']};
        --muted: {p['muted']};
    }}
    """
    st.markdown(f"<style>{root_vars}{STATIC_CSS}</style>", unsafe_allow_html=True)


inject_css(st.session_state.theme)


# ============================================================
# HELPERS: badges, priority, internal/external guidance
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
    """
    Lightweight heuristic priority estimate (not part of the trained
    model) based on keywords, category sensitivity, and how confident/
    escalated the ticket already is.
    """
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


# ============================================================
# SESSION STATE
# ============================================================

if "history" not in st.session_state:
    st.session_state.history = []
if "accepted" not in st.session_state:
    st.session_state.accepted = set()
if "escalated_by_agent" not in st.session_state:
    st.session_state.escalated_by_agent = set()
if "example_ticket" not in st.session_state:
    st.session_state.example_ticket = ""
if "page" not in st.session_state:
    st.session_state.page = "🎫 Submit Ticket"
if "username" not in st.session_state:
    st.session_state.username = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_org" not in st.session_state:
    st.session_state.user_org = ""

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


# ============================================================
# LOGIN PAGE
# ============================================================

def page_login():
    st.markdown(
        """
        <div style="text-align:center; margin-top: 8vh;">
            <div style="font-size:3rem; font-weight:900; font-family:'Space Grotesk', sans-serif;
                        background: linear-gradient(90deg, var(--cyan), var(--magenta), var(--gold));
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                        letter-spacing: -1px;">
                🧠 Resolve IQ
            </div>
            <div style="color:var(--muted); font-size:1.05rem; margin-top:6px;">
                AI-Powered Intelligent Ticket Routing &amp; Resolution Agent
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown("### 👋 Sign in to continue")

        name = st.text_input("Your name", placeholder="e.g. Priya Sharma")
        user_id = st.text_input("Employee / Student ID", placeholder="e.g. EMP1042")
        org = st.text_input("Organization name", placeholder="e.g. Acme Corp")

        if st.button("🚀 Enter Dashboard", use_container_width=True):
            if name.strip():
                st.session_state.logged_in = True
                st.session_state.username = name.strip()
                st.session_state.user_id = user_id.strip()
                st.session_state.user_org = org.strip()
                st.rerun()
            else:
                st.warning("Please enter your name at least.")

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
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🧠 Resolve IQ")
    st.caption("AI-powered routing, RAG resolution & remediation")

    st.markdown(
        f"👤 **{st.session_state.username}**"
        + (f"  \nID: {st.session_state.user_id}" if st.session_state.user_id else "")
        + (f"  \n🏢 {st.session_state.user_org}" if st.session_state.user_org else "")
    )
    if st.button("🔓 Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")

    PAGES = ["🎫 Submit Ticket", "📜 History", "📊 Analytics"]
    st.session_state.page = st.radio(
        "Navigate", PAGES, index=PAGES.index(st.session_state.page), label_visibility="collapsed",
    )

    st.markdown("---")
    st.metric("Tickets Processed", len(st.session_state.history))

    theme_label = "☀️ Switch to Light" if st.session_state.theme == "dark" else "🌙 Switch to Dark"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.accepted = set()
        st.session_state.escalated_by_agent = set()
        st.session_state.example_ticket = ""
        st.rerun()


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
# PAGE: SUBMIT TICKET
# ============================================================

def page_submit():
    st.markdown("# Resolve IQ")
    st.caption("Classification • RAG Retrieval • Confidence • Remediation • Escalation")

    st.markdown("### 🔄 Submit a new ticket")

    mode = st.radio(
        "What kind of thing are you submitting?",
        ["🎫 IT Support Ticket", "🧭 General / Other Query"],
        horizontal=True,
        help="Use General/Other for anything that isn't a standard IT ticket — "
             "it skips forced auto-classification and goes straight to a human.",
    )

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

    submitted = st.button("🚀 Analyze Ticket", use_container_width=True)

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

        # Priority estimate (heuristic, not from the trained model)
        result.priority = estimate_priority(
            ticket_text, result.classification.category, result.confidence.tier, result.escalated
        )

        # Optional attachment — saved to disk, name/size kept on the result
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

        # ---- Manual override ----
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

        # ---- Internal vs External diagnosis ----
        st.markdown("### 🛠️ Diagnosis & Fix")
        remediation = result.remediation
        scope = diagnose_scope(result.classification.category, remediation)

        st.markdown(scope_badge(scope), unsafe_allow_html=True)
        st.markdown('<div class="glow-card">', unsafe_allow_html=True)
        for line in guidance_lines(remediation, scope):
            if line:
                st.markdown(line)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 💡 Suggested Resolution")
        st.info(result.resolution.suggested_steps)

        if result.recurring.is_recurring:
            st.warning(f"🔁 **Recurring issue detected** — {result.recurring.cluster_size} related tickets found in history.")
        else:
            st.success("🔹 No significant recurring pattern detected.")

        if result.retrieved:
            with st.expander("📚 Similar historical tickets used for this suggestion"):
                for t in result.retrieved:
                    st.markdown(f"**{t.ticket_id}** — similarity {t.similarity:.0%}")
                    st.caption(t.text)
                    if t.resolution:
                        st.write(f"Resolution: {t.resolution}")
                    st.markdown("---")


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

    headers = ["ticket_id", "category", "department", "priority", "tier", "escalated", "recurring", "text"]
    widths = [18, 26, 34, 16, 16, 16, 16, 130]

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
# PAGE: HISTORY
# ============================================================

def page_history():
    st.markdown("# 📜 Ticket History")
    history = st.session_state.history

    if not history:
        st.info("No tickets processed yet. Go to **Submit Ticket** to analyze your first one.")
        return

    # ---- Search & filter ----
    st.markdown("### 🔍 Search & Filter")
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
    render_export_buttons(history_to_rows(filtered), key_prefix="history")

    high = sum(1 for r in filtered if r.confidence.tier.lower() == "high")
    medium = sum(1 for r in filtered if r.confidence.tier.lower() == "medium")
    low = sum(1 for r in filtered if r.confidence.tier.lower() == "low")
    escalated = sum(1 for r in filtered if r.escalated)

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟢 High Confidence", high)
    m2.metric("🟡 Medium Confidence", medium)
    m3.metric("🔴 Low Confidence", low)
    m4.metric("🚨 Escalated", escalated)

    st.markdown("---")

    for result in filtered:
        ticket_id = result.ticket.id
        tier = result.confidence.tier.upper()
        priority = getattr(result, "priority", "Medium")

        with st.expander(f"🎫 {ticket_id}  |  {result.classification.category}  |  {tier}  |  {priority}"):
            h1, h2, h3, h4 = st.columns(4)
            h1.metric("Category", result.classification.category)
            h2.metric("Department", result.routing.department)
            h3.metric("Confidence", f"{result.confidence.score:.0%}")
            h4.metric("Status", "ESCALATED" if result.escalated else "PROCESSED")

            st.markdown(priority_badge(priority), unsafe_allow_html=True)
            if result.ticket.user:
                st.caption(f"👤 Submitted by: {result.ticket.user}")
            if getattr(result, "attachment", None):
                st.caption(f"📎 Attached: {result.attachment['name']}")

            st.write(f"**Ticket text:** {result.ticket.text}")

            remediation = result.remediation
            scope = diagnose_scope(result.classification.category, remediation)
            st.markdown(scope_badge(scope), unsafe_allow_html=True)
            st.caption(remediation.get("message", ""))

            if result.recurring.is_recurring:
                st.warning(f"🔁 Recurring — {result.recurring.cluster_size} related tickets")

            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("✅ Accept", key=f"accept_{ticket_id}", use_container_width=True):
                    st.session_state.accepted.add(ticket_id)
            with a2:
                if st.button("🚨 Escalate", key=f"escalate_{ticket_id}", use_container_width=True):
                    st.session_state.escalated_by_agent.add(ticket_id)
                    st.warning("Ticket marked for human escalation.")
            with a3:
                st.write("")

            if ticket_id in st.session_state.accepted:
                st.success("Marked as accepted ✅")
            if ticket_id in st.session_state.escalated_by_agent:
                st.error("Marked for human escalation 🚨")

            st.text_area("Investigation notes", key=f"notes_{ticket_id}", height=70)


# ============================================================
# PAGE: ANALYTICS
# ============================================================

def page_analytics():
    st.markdown("# 📊 Analytics")
    history = st.session_state.history

    if not history:
        st.info("No data yet. Process some tickets first from **Submit Ticket**.")
        return

    avg_confidence = sum(r.confidence.score for r in history) / len(history)
    recurring_count = sum(1 for r in history if r.recurring.is_recurring)
    accepted_count = len(st.session_state.accepted)
    agent_escalations = len(st.session_state.escalated_by_agent)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🎯 Avg Confidence", f"{avg_confidence:.0%}")
    k2.metric("🔁 Recurring Candidates", recurring_count)
    k3.metric("✅ Accepted", accepted_count)
    k4.metric("👨‍💻 Agent Escalations", agent_escalations)

    st.markdown("---")
    st.markdown("### 🗂️ Tickets by Category")
    category_counts = {}
    for result in history:
        category_counts[result.classification.category] = category_counts.get(result.classification.category, 0) + 1

    max_count = max(category_counts.values())
    palette = ["#00e5ff", "#ff3fa4", "#8b5cf6", "#ffb020", "#22e0a3", "#ff4d6d", "#38bdf8"]
    for i, (category, count) in enumerate(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)):
        color = palette[i % len(palette)]
        pct = count / max_count
        st.markdown(
            f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; font-weight:700; margin-bottom:4px;">
                    <span>{category}</span><span>{count} ticket(s)</span>
                </div>
                <div style="background:var(--panel-2); border-radius:8px; height:14px; overflow:hidden;">
                    <div style="width:{pct*100:.0f}%; height:100%; background:{color};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 🚦 Tickets by Priority")
    priority_counts = {"Urgent": 0, "High": 0, "Medium": 0, "Low": 0}
    for result in history:
        priority_counts[getattr(result, "priority", "Medium")] += 1
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("🔴 Urgent", priority_counts["Urgent"])
    p2.metric("🟠 High", priority_counts["High"])
    p3.metric("🔵 Medium", priority_counts["Medium"])
    p4.metric("🟢 Low", priority_counts["Low"])

    st.markdown("---")
    st.markdown("### 🏢 Tickets by Department")
    routing_counts = {}
    for result in history:
        routing_counts[result.routing.department] = routing_counts.get(result.routing.department, 0) + 1
    for department, count in sorted(routing_counts.items(), key=lambda x: x[1], reverse=True):
        st.write(f"**{department}** — {count} ticket(s)")

    st.markdown("---")
    st.markdown("### 🛠️ Internal vs External vs Human")
    scopes = {"internal": 0, "external": 0, "needs_human": 0}
    for result in history:
        scopes[diagnose_scope(result.classification.category, result.remediation)] += 1
    s1, s2, s3 = st.columns(3)
    s1.metric("🤖 Fixed Internally", scopes["internal"])
    s2.metric("🚫 Needs External Action", scopes["external"])
    s3.metric("👤 Needs Human Agent", scopes["needs_human"])

    st.markdown("---")
    st.markdown("### 📤 Export Everything")
    render_export_buttons(history_to_rows(history), key_prefix="analytics")


# ============================================================
# ROUTER
# ============================================================

if st.session_state.page == "🎫 Submit Ticket":
    page_submit()
elif st.session_state.page == "📜 History":
    page_history()
else:
    page_analytics()


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
