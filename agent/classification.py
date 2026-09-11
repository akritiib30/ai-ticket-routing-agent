import re
from pathlib import Path

import joblib

from .models import ClassificationResult


# ============================================================
# ENTERPRISE CATEGORY NORMALIZATION
# ============================================================
# The trained model may contain legacy category names.
# Normalize them into the current Resolve IQ enterprise taxonomy.

CATEGORY_NORMALIZATION = {
    "Network": "Network & Connectivity",
    "Access Management": "Account & Access",
    "Application": "Software & Applications",
    "Security": "Security Operations",
    "Infrastructure": "Infrastructure & Servers",
    "Database": "Database & Storage",
    "Storage": "Storage & Files",
}


class Classifier:
    """
    Hybrid hierarchical ticket classifier.

    Uses high-precision intent rules for common enterprise issues
    and falls back to the trained TF-IDF + Logistic Regression model
    when no specific intent is detected.
    """

    def __init__(self, seed_tickets=None):
        model_path = (
            Path(__file__).parent
            / "data"
            / "ticket_classifier.joblib"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at: {model_path}"
            )

        self.model = joblib.load(model_path)
        self.categories = list(self.model.classes_)

    # ============================================================
    # HIERARCHICAL INTENT DETECTION
    # ============================================================

    def _detect_hierarchical_intent(self, text: str):
        """
        Detect a precise enterprise ticket intent.

        Returns:
            (category, subcategory, issue_type, confidence)

        or:
            None
        """

        tl = (text or "").lower().strip()

        # Empty text should fall through to the ML model.
        if not tl:
            return None

        # --------------------------------------------------------
        # 1. VPN
        # --------------------------------------------------------

        if re.search(r"\bvpn\b", tl):
            return (
                "Network & Connectivity",
                "VPN",
                "VPN Connection",
                0.94,
            )

        # --------------------------------------------------------
        # 2. Wi-Fi
        # --------------------------------------------------------

        if re.search(
            r"\b(wi[\s\-_]?fi|wireless|wlan)\b",
            tl,
        ):
            return (
                "Network & Connectivity",
                "Wi-Fi",
                "Wi-Fi Connectivity",
                0.92,
            )

        # --------------------------------------------------------
        # 3. Slow Network / Bandwidth
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"slow\s+(network|internet|connection)"
            r"|latency"
            r"|packet\s*loss"
            r")\b",
            tl,
        ):
            return (
                "Network & Connectivity",
                "Bandwidth",
                "Slow Network Performance",
                0.89,
            )

        # --------------------------------------------------------
        # 4. Password Reset
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"reset\s+(my\s+)?password"
            r"|password\s+reset"
            r"|forgot\s+password"
            r"|change\s+password"
            r")\b",
            tl,
        ):
            return (
                "Account & Access",
                "Password",
                "Password Reset",
                0.95,
            )

        # --------------------------------------------------------
        # 5. Account Locked
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"account\s+(is\s+)?locked"
            r"|locked\s+out"
            r"|lockout"
            r"|account\s+lock"
            r")\b",
            tl,
        ):
            return (
                "Account & Access",
                "Authentication",
                "Account Lock",
                0.94,
            )

        # --------------------------------------------------------
        # 6. Cannot Login
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"can'?t\s+log\s*in"
            r"|cannot\s+log\s*in"
            r"|unable\s+to\s+log\s*in"
            r"|login\s+fail"
            r"|login\s+issue"
            r"|sign\s*in\s+issue"
            r")\b",
            tl,
        ):
            return (
                "Account & Access",
                "Authentication",
                "Login Failure",
                0.93,
            )

        # --------------------------------------------------------
        # 7. FILE ACCESS / SHARED DRIVE
        # --------------------------------------------------------
        # IMPORTANT:
        # This is deliberately checked BEFORE generic
        # "permission denied" so:
        #
        # "shared drive access denied"
        #
        # remains a Storage & Files issue rather than being
        # incorrectly classified as Account & Access.

        if re.search(
            r"\b("
            r"file\s+access"
            r"|shared\s+drive"
            r"|shared\s+folder"
            r"|network\s+drive"
            r"|smb\s+share"
            r"|mapped\s+drive"
            r")\b",
            tl,
        ):
            return (
                "Storage & Files",
                "Shared Drives",
                "File Permissions",
                0.90,
            )

        # --------------------------------------------------------
        # 8. Permission Denied / Access Request
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"permission\s+denied"
            r"|access\s+denied"
            r"|forbidden"
            r"|request\s+access"
            r"|access\s+request"
            r"|unauthorized"
            r")\b",
            tl,
        ):
            return (
                "Account & Access",
                "Permissions",
                "Access Denied",
                0.91,
            )

        # --------------------------------------------------------
        # 9. Email / Collaboration
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"email"
            r"|outlook"
            r"|inbox"
            r"|exchange"
            r"|mailbox"
            r"|webmail"
            r")\b",
            tl,
        ):
            return (
                "Email & Collaboration",
                "Email",
                "Email Access",
                0.92,
            )

        # --------------------------------------------------------
        # 10. Server Unavailable / Outage
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"server\s+(is\s+)?("
            r"unavailable"
            r"|down"
            r"|unreachable"
            r"|offline"
            r")"
            r"|host\s+down"
            r")\b",
            tl,
        ):
            return (
                "Infrastructure & Servers",
                "Server Availability",
                "Service Unavailable",
                0.92,
            )

        # --------------------------------------------------------
        # 11. Database
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"database"
            r"|postgres"
            r"|mysql"
            r"|oracle"
            r"|sql\s+server"
            r"|db\s+connection"
            r"|db\s+access"
            r")\b",
            tl,
        ):
            return (
                "Database & Storage",
                "Database Access",
                "Database Connection",
                0.91,
            )

        # --------------------------------------------------------
        # 12. Printer
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"printer"
            r"|print\s+job"
            r"|paper\s*jam"
            r"|spooler"
            r")\b",
            tl,
        ):
            return (
                "Hardware & Peripherals",
                "Printer",
                "Printer Hardware",
                0.93,
            )

        # --------------------------------------------------------
        # 13. Application Error / Crash / Launch Failure
        # --------------------------------------------------------

        if re.search(
            r"\b("
            r"application"
            r"|software"
            r"|app\s+crash"
            r"|crash"
            r"|not\s+opening"
            r"|fails?\s+to\s+launch"
            r"|error\s+code"
            r")\b",
            tl,
        ):
            return (
                "Software & Applications",
                "Application Failure",
                "Application Launch",
                0.90,
            )

        return None

    # ============================================================
    # PUBLIC PREDICTION METHOD
    # ============================================================

    def predict(self, text: str) -> ClassificationResult:
        """
        Predict category, subcategory, issue type, and confidence.

        Specific high-confidence intent rules are preferred.
        Otherwise the trained ML classifier is used.
        """

        # --------------------------------------------------------
        # First: high-precision hierarchical rules
        # --------------------------------------------------------

        intent = self._detect_hierarchical_intent(text)

        if intent:
            category, subcategory, issue_type, confidence = intent

            return ClassificationResult(
                category=category,
                confidence=confidence,
                subcategory=subcategory,
                issue_type=issue_type,
            )

        # --------------------------------------------------------
        # Fallback: trained ML model
        # --------------------------------------------------------

        raw_pred = self.model.predict([text])[0]

        probabilities = self.model.predict_proba([text])[0]
        confidence = float(max(probabilities))

        normalized_category = CATEGORY_NORMALIZATION.get(
            raw_pred,
            raw_pred,
        )

        return ClassificationResult(
            category=normalized_category,
            confidence=round(confidence, 4),
            subcategory="General",
            issue_type="Standard Request",
        )