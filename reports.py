"""
Resolve IQ - Export Reports Generator (CSV & PDF)
Provides PDF report generation using fpdf2 and CSV exports.
"""

import io
import csv
from datetime import datetime
from fpdf import FPDF


def sanitize_text(text) -> str:
    """Sanitize strings so standard PDF core fonts (Helvetica) render without Latin-1 codec crashes."""
    if text is None:
        return ""
    s = str(text)
    # Replace common typographic Unicode characters with ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u2022": "*",
        "\u00a0": " ", "\u2030": "%", "\u2122": "TM", "\u00ae": "(R)",
        "\u00a9": "(C)", "\u2713": "[OK]", "\u2717": "[X]", "\u25b6": ">",
        "\u26a0": "[!]", "\u2605": "*", "\u25cf": "*", "\u2197": "->",
        "\u21ba": "[R]", "\u2295": "+", "\u25c9": "o", "\u23f1": "Time:"
    }
    for orig, rep in replacements.items():
        s = s.replace(orig, rep)
    # Encode to latin-1 replacing unknown chars with '?'
    return s.encode("latin-1", errors="replace").decode("latin-1")


def generate_csv(tickets: list) -> bytes:
    """Generate CSV bytes containing full ticket data."""
    output = io.StringIO()
    fields = [
        "ticket_id", "timestamp", "username", "organization", "subject", "description",
        "priority", "category", "classification", "classification_confidence",
        "routing", "confidence", "confidence_tier", "resolution", "remediation",
        "recurring", "escalated", "status", "handling_decision", "resolution_ownership", "attachment_name"
    ]

    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    for t in tickets:
        row = dict(t)
        # Format complex fields for clean CSV reading
        if isinstance(row.get("remediation"), dict):
            row["remediation"] = row["remediation"].get("message") or row["remediation"].get("action", "")
        if isinstance(row.get("classification_confidence"), (float, int)):
            row["classification_confidence"] = f"{float(row['classification_confidence']) * 100:.1f}%"
        if isinstance(row.get("confidence"), (float, int)):
            row["confidence"] = f"{float(row['confidence']) * 100:.1f}%"
        writer.writerow(row)

    # Use UTF-8-SIG so Excel opens Unicode properly
    return output.getvalue().encode("utf-8-sig")


class ResolveIQPDF(FPDF):
    """Custom styled PDF for Resolve IQ reports."""
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 41, 59)
        self.cell(0, 8, "RESOLVE IQ", ln=1)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4, "AI-Powered Ticket Intelligence & Resolution System", ln=1)
        self.line(10, 22, self.w - 10, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(0, 6, f"Page {self.page_no()} of {{nb}}  |  Confidential  |  Resolve IQ Support Platform", align="C")


def generate_all_tickets_pdf(tickets: list) -> bytes:
    """Generate a landscape PDF table summary of all tickets."""
    pdf = ResolveIQPDF(orientation="L", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    # Document Title
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, sanitize_text("Ticket Queue & Operations Summary Report"), ln=1)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(100, 116, 139)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 5, sanitize_text(f"Generated: {now_str}  |  Total Tickets Analyzed: {len(tickets)}"), ln=1)
    pdf.ln(3)

    # Table Header
    headers = [
        ("TICKET ID", 28),
        ("DATE / TIME", 32),
        ("USER", 30),
        ("SUBJECT", 68),
        ("CATEGORY", 28),
        ("PRIORITY", 20),
        ("DEPARTMENT", 38),
        ("CONF.", 16),
        ("STATUS", 22),
    ]

    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(30, 41, 59)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("Helvetica", "B", 7.5)

    for title, width in headers:
        pdf.cell(width, 7, title, border=1, fill=True, align="C")
    pdf.ln()

    # Table Rows
    pdf.set_font("Helvetica", "", 7.5)
    for i, t in enumerate(tickets):
        fill = (i % 2 == 1)
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(51, 65, 85)

        tid = sanitize_text(t.get("ticket_id", ""))[:14]
        date = sanitize_text(t.get("timestamp", ""))[:16]
        user = sanitize_text(t.get("username", ""))[:18]
        subj = sanitize_text(t.get("subject", ""))[:42]
        cat = sanitize_text(t.get("category", ""))[:16]
        prio = sanitize_text(t.get("priority", ""))[:10]
        dept = sanitize_text(t.get("routing", ""))[:22]
        conf_val = float(t.get("confidence", 0.0))
        conf = f"{conf_val * 100:.0f}%"
        status = sanitize_text(t.get("status", "Open"))[:12]

        pdf.cell(28, 6.5, tid, border=1, fill=fill)
        pdf.cell(32, 6.5, date, border=1, fill=fill)
        pdf.cell(30, 6.5, user, border=1, fill=fill)
        pdf.cell(68, 6.5, subj, border=1, fill=fill)
        pdf.cell(28, 6.5, cat, border=1, fill=fill)
        pdf.cell(20, 6.5, prio, border=1, fill=fill, align="C")
        pdf.cell(38, 6.5, dept, border=1, fill=fill)
        pdf.cell(16, 6.5, conf, border=1, fill=fill, align="C")
        pdf.cell(22, 6.5, status, border=1, fill=fill, align="C")
        pdf.ln()

    return bytes(pdf.output())


def generate_single_ticket_pdf(t: dict) -> bytes:
    """Generate a portrait detailed dossier PDF for a single ticket."""
    pdf = ResolveIQPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    tid = sanitize_text(t.get("ticket_id", "N/A"))
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(120, 8, f"Ticket Analysis Dossier: #{tid}", ln=0)

    # Status badge on top right
    status = sanitize_text(t.get("status", "Open")).upper()
    pdf.set_font("Helvetica", "B", 9)
    if t.get("escalated"):
        pdf.set_fill_color(254, 226, 226)
        pdf.set_text_color(185, 28, 28)
    elif status == "RESOLVED":
        pdf.set_fill_color(220, 252, 231)
        pdf.set_text_color(21, 128, 61)
    else:
        pdf.set_fill_color(254, 243, 199)
        pdf.set_text_color(180, 83, 9)

    pdf.cell(0, 8, f"  {status}  ", border=1, fill=True, align="C", ln=1)
    pdf.ln(2)

    # Metadata Grid
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(71, 85, 105)

    left_w = 95
    right_w = 95

    pdf.cell(left_w, 6, sanitize_text(f"User: {t.get('username', 'Unknown')}"), border="LT", fill=True)
    pdf.cell(right_w, 6, sanitize_text(f"Priority: {t.get('priority', 'Medium')}"), border="RT", fill=True, ln=1)

    pdf.cell(left_w, 6, sanitize_text(f"Organization: {t.get('organization', 'N/A')}"), border="L", fill=True)
    pdf.cell(right_w, 6, sanitize_text(f"Department: {t.get('routing', 'General IT')}"), border="R", fill=True, ln=1)

    pdf.cell(left_w, 6, sanitize_text(f"Timestamp: {t.get('timestamp', 'N/A')}"), border="L", fill=True)
    pdf.cell(right_w, 6, sanitize_text(f"Attachment: {t.get('attachment_name') or 'None'}"), border="R", fill=True, ln=1)

    pdf.cell(left_w, 6, sanitize_text(f"Handling Decision: {t.get('handling_decision', 'Accepted')}"), border="LB", fill=True)
    pdf.cell(right_w, 6, sanitize_text(f"Resolution Ownership: {t.get('resolution_ownership', 'AI Resolution Available')}"), border="RB", fill=True, ln=1)

    pdf.ln(4)

    # Issue Subject & Description
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "1. Issue Summary & Description", ln=1)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 5, sanitize_text(f"Subject: {t.get('subject', 'No subject provided')}"), ln=1)

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4.5, sanitize_text(t.get("description", "No detailed description.")))
    pdf.ln(3)

    # AI Classification & Confidence
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "2. AI Classification & Confidence Assessment", ln=1)

    conf_score = float(t.get("confidence", 0.0))
    conf_tier = sanitize_text(t.get("confidence_tier", "medium")).capitalize()
    class_cat = sanitize_text(t.get("classification", t.get("category", "General")))

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 5, sanitize_text(f"Predicted Category: {class_cat}  |  Confidence: {conf_score * 100:.1f}% ({conf_tier} Tier)"), ln=1)
    pdf.cell(0, 5, sanitize_text(f"Target Department Routing: {t.get('routing', 'General IT Support')}"), ln=1)
    pdf.ln(3)

    # Similar Tickets / RAG Retrieval
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "3. Knowledge Base / RAG Retrieval", ln=1)

    rag_results = t.get("rag_results", [])
    if rag_results and isinstance(rag_results, list):
        pdf.set_font("Helvetica", "", 7.5)
        for r in rag_results[:3]:
            rtid = sanitize_text(r.get("ticket_id") or r.get("id") or "Seed")
            rsim = float(r.get("similarity", 0.0))
            rtext = sanitize_text(r.get("text", ""))[:120]
            rres = sanitize_text(r.get("resolution", ""))[:120]
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 4.5, f"* [{rtid}] (Relevance: {rsim * 100:.0f}%): {rtext}", ln=1)
            if rres:
                pdf.set_text_color(100, 116, 139)
                pdf.cell(0, 4.5, f"   Resolution: {rres}", ln=1)
    else:
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, "No previous similar tickets matched.", ln=1)
    pdf.ln(3)

    # Resolution Recommendation
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "4. AI Recommended Resolution", ln=1)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    res_text = sanitize_text(t.get("resolution", "No resolution generated."))
    pdf.multi_cell(0, 4.5, res_text)
    pdf.ln(3)

    # Automated Remediation
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "5. Safe Automated Remediation", ln=1)

    remed = t.get("remediation", {})
    if isinstance(remed, dict):
        diag = sanitize_text(remed.get("diagnosis", "Diagnostic evaluated"))
        act = sanitize_text(remed.get("action", "Safe automated check"))
        msg = sanitize_text(remed.get("message", "No remediation performed."))
        succ = "SUCCESS" if remed.get("success") else "SAFETY BOUNDARY / HUMAN ATTENTION"
    else:
        diag = "Diagnostic evaluated"
        act = "N/A"
        msg = sanitize_text(str(remed))
        succ = "N/A"

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 4.5, f"Diagnosis: {diag}", ln=1)
    pdf.cell(0, 4.5, f"Action: {act}  |  Outcome: {succ}", ln=1)
    pdf.multi_cell(0, 4.5, f"Details: {msg}")
    pdf.ln(3)

    # Recurring Issue & Escalation Decision
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "6. Escalation & Recurring Pattern Decision", ln=1)

    pdf.set_font("Helvetica", "", 8)
    is_rec = "DETECTED (Frequent pattern across historical tickets)" if t.get("recurring") else "NO recurring pattern detected"
    rec_size = t.get("recurring_details", {}).get("cluster_size", 0) if isinstance(t.get("recurring_details"), dict) else 0
    pdf.cell(0, 4.5, sanitize_text(f"Recurring Issue Check: {is_rec} (Cluster Size: {rec_size})"), ln=1)

    if t.get("escalated"):
        esc_text = "ESCALATION REQUIRED - Ticket is designated for human specialist review."
    elif t.get("confidence_tier") == "medium":
        esc_text = "NO ESCALATION - Ticket remains in standard queue handling; human review can be applied if needed."
    elif t.get("confidence_tier") == "low":
        esc_text = "NO ESCALATION FLAG STORED - Low-confidence tickets should be reviewed before resolution."
    else:
        esc_text = "NO ESCALATION - Ticket met the current escalation threshold; resolution still requires operational confirmation."

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, sanitize_text(f"Escalation Status: {esc_text}"), ln=1)

    return bytes(pdf.output())
