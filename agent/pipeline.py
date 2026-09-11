"""Resolve IQ - Ticket Processing Pipeline.

Orchestrates the full ticket lifecycle:

Submission
    -> Preprocessing
    -> Classification
    -> Routing
    -> RAG Retrieval
    -> Resolution Suggestion
    -> Confidence Check
    -> Remediation Safety Check
    -> Recurring Detection
    -> Escalation

Each stage remains separated into its own module so individual components
can be changed independently.
"""

from datetime import datetime

from . import (
    preprocessing,
    routing,
    resolution,
    confidence as confidence_mod,
    escalation,
    recurring,
)
from .classification import Classifier
from .retrieval import Retriever
from .knowledge_base import load_seed_tickets
from .models import Ticket, PipelineResult


# ------------------------------------------------------------------
# SAFETY BOUNDARY
# ------------------------------------------------------------------
# These categories must never be treated as automatically remediable.
# We support both the current enterprise taxonomy and legacy names so
# the safety boundary remains effective even if an older category name
# appears somewhere in the application.
EXTERNAL_CATEGORIES = {
    # Current enterprise taxonomy
    "Security Operations",
    "Account & Access",
    "Database & Storage",

    # Legacy taxonomy
    "Security",
    "Access Management",
    "Database",
}


def build_remediation(category: str, confidence_result) -> dict:
    """Build the remediation status for the pipeline result.

    Important:
    This function describes whether an automated remediation/check is
    allowed. It does NOT claim that a real infrastructure change was
    executed unless an actual remediation implementation performs it.
    """

    tier = getattr(confidence_result, "tier", "medium")
    score = getattr(confidence_result, "score", 0.0)

    # --------------------------------------------------------------
    # SAFETY BOUNDARY
    # --------------------------------------------------------------
    if category in EXTERNAL_CATEGORIES:
        return {
            "diagnosis": (
                f"{category} issue detected. "
                "This category requires controlled human handling."
            ),
            "action": "No automated remediation performed.",
            "success": False,
            "message": (
                "This category is intentionally excluded from automatic "
                "remediation. Route the ticket to the appropriate owning "
                "team for controlled handling."
            ),
        }

    # --------------------------------------------------------------
    # HIGH CONFIDENCE
    # --------------------------------------------------------------
    if tier == "high":
        return {
            "diagnosis": (
                f"{category} issue classified with high confidence "
                f"({score:.0%})."
            ),
            "action": (
                "Automated remediation eligibility confirmed; "
                "no destructive action performed."
            ),
            "success": True,
            "message": (
                "The ticket meets the confidence threshold for the "
                "supported automated workflow. The recommended resolution "
                "can proceed through the approved handling path."
            ),
        }

    # --------------------------------------------------------------
    # MEDIUM / LOW CONFIDENCE
    # --------------------------------------------------------------
    return {
        "diagnosis": (
            f"{category} issue classified with {tier} confidence "
            f"({score:.0%})."
        ),
        "action": "No automatic remediation performed.",
        "success": False,
        "message": (
            "Confidence is not high enough for automatic remediation. "
            "A human agent should review and confirm the recommended "
            "resolution before taking action."
        ),
    }


class TicketAgentPipeline:
    """Run the complete Resolve IQ ticket intelligence pipeline."""

    def __init__(self):
        seed_tickets = load_seed_tickets()

        self.classifier = Classifier(seed_tickets)
        self.retriever = Retriever(seed_tickets)

    def run(
        self,
        ticket_id: str,
        raw_text: str,
        user: str = None,
    ) -> PipelineResult:
        """Process one ticket through all pipeline stages."""

        # ----------------------------------------------------------
        # 1. CREATE TICKET
        # ----------------------------------------------------------
        ticket = Ticket(
            id=ticket_id,
            text=raw_text,
            submitted_at=datetime.utcnow(),
            user=user,
        )

        # ----------------------------------------------------------
        # 2. PREPROCESS
        # ----------------------------------------------------------
        clean_text = preprocessing.preprocess(raw_text)

        # ----------------------------------------------------------
        # 3. CLASSIFY
        # ----------------------------------------------------------
        classification_result = self.classifier.predict(clean_text)

        # ----------------------------------------------------------
        # 4. ROUTE
        # ----------------------------------------------------------
        routing_result = routing.route(
            classification_result.category
        )

        # ----------------------------------------------------------
        # 5. RETRIEVE SIMILAR HISTORICAL TICKETS
        # ----------------------------------------------------------
        retrieved = self.retriever.search(
            clean_text,
            top_k=3,
        )

        # ----------------------------------------------------------
        # 6. GENERATE RESOLUTION SUGGESTION
        # ----------------------------------------------------------
        resolution_result = resolution.generate(
            clean_text,
            retrieved,
        )

        # ----------------------------------------------------------
        # 7. ASSESS CONFIDENCE
        # ----------------------------------------------------------
        confidence_result = confidence_mod.assess(
            classification_result,
            retrieved,
        )

        # ----------------------------------------------------------
        # 8. BUILD REMEDIATION SAFETY RESULT
        # ----------------------------------------------------------
        remediation = build_remediation(
            classification_result.category,
            confidence_result,
        )

        # ----------------------------------------------------------
        # 9. DETECT RECURRING ISSUE
        # ----------------------------------------------------------
        recurring_flag = recurring.detect(retrieved)

        # ----------------------------------------------------------
        # 10. ESCALATION
        # ----------------------------------------------------------
        escalated = escalation.should_escalate(
            confidence_result
        )

        # ----------------------------------------------------------
        # 11. BUILD FINAL RESULT
        # ----------------------------------------------------------
        # remediation is passed directly into PipelineResult.
        # This fixes the missing-required-argument error.
        return PipelineResult(
            ticket=ticket,
            classification=classification_result,
            routing=routing_result,
            retrieved=retrieved,
            resolution=resolution_result,
            confidence=confidence_result,
            recurring=recurring_flag,
            escalated=escalated,
            remediation=remediation,
        )