"""
Resolve IQ - Safe Automated Remediation

Provides low-risk diagnostics and corrective actions for supported
IT categories.

Safety rules:
- Passwords are never changed automatically.
- Accounts are never modified automatically.
- Permissions are never changed automatically.
- Security settings are never modified automatically.
- Database data/schema is never modified automatically.
- Files are never deleted automatically.
- Diagnostic success is not reported as a successful fix.
"""

import platform
import shutil
import subprocess


# ============================================================
# COMMAND EXECUTION
# ============================================================

def run_command(command, timeout=15):
    """Run a system command safely and return its result."""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
        }

    except Exception as exc:
        return {
            "success": False,
            "output": "",
            "error": str(exc),
        }


# ============================================================
# NETWORK DIAGNOSTIC
# ============================================================

def test_internet():
    """Check whether the current machine can reach the internet."""

    system = platform.system()

    if system == "Windows":
        command = ["ping", "-n", "1", "8.8.8.8"]
    else:
        command = ["ping", "-c", "1", "8.8.8.8"]

    return run_command(command, timeout=10)


# ============================================================
# MAIN REMEDIATION FUNCTION
# ============================================================

def diagnose_and_fix(category: str, text: str):
    """
    Diagnose a ticket and perform only approved low-risk actions.

    Returns:
        dict:
            diagnosis
            action
            success
            message

    `success` means an actual corrective action succeeded.
    A diagnostic check succeeding does NOT mean the ticket was fixed.
    """

    category = (category or "").strip()
    text_lower = (text or "").lower()

    # ============================================================
    # NETWORK / CONNECTIVITY
    # ============================================================

    if category in {
        "Network & Connectivity",
        "Network",
    }:

        # --------------------------------------------------------
        # VPN
        # --------------------------------------------------------

        if "vpn" in text_lower:
            return {
                "diagnosis": "VPN connectivity issue",
                "action": "VPN connection requires verification",
                "success": False,
                "message": (
                    "The system identified a VPN-related issue, but VPN "
                    "credentials and corporate VPN configuration cannot be "
                    "modified automatically. Reconnect to the company VPN "
                    "or escalate to Network Support."
                ),
            }

        # --------------------------------------------------------
        # Wi-Fi / Internet / Connectivity
        # --------------------------------------------------------

        if any(
            word in text_lower
            for word in [
                "wifi",
                "wi-fi",
                "internet",
                "connection",
                "connectivity",
                "network",
            ]
        ):

            system = platform.system()

            # ----------------------------------------------------
            # Windows
            # ----------------------------------------------------

            if system == "Windows":

                before_test = test_internet()

                # Internet is already working.
                # This is a successful diagnostic, NOT a successful fix.
                if before_test["success"]:
                    return {
                        "diagnosis": "Network connectivity checked",
                        "action": "Connectivity test completed",
                        "success": False,
                        "message": (
                            "Internet connectivity is currently working. "
                            "No corrective action was required."
                        ),
                    }

                # ------------------------------------------------
                # Attempt safe DNS cache cleanup
                # ------------------------------------------------

                dns_result = run_command(
                    ["ipconfig", "/flushdns"],
                    timeout=10,
                )

                # ------------------------------------------------
                # Test again after corrective action
                # ------------------------------------------------

                after_test = test_internet()

                if after_test["success"]:
                    return {
                        "diagnosis": "Network/DNS connectivity issue",
                        "action": "DNS cache cleared and connectivity restored",
                        "success": True,
                        "message": (
                            "The DNS cache was cleared successfully and "
                            "internet connectivity was restored."
                        ),
                    }

                if dns_result["success"]:
                    return {
                        "diagnosis": "Network connectivity issue",
                        "action": "DNS cache cleared; connectivity re-tested",
                        "success": False,
                        "message": (
                            "The DNS cache was cleared, but internet "
                            "connectivity is still unavailable. Further "
                            "network investigation is required."
                        ),
                    }

                return {
                    "diagnosis": "Network connectivity issue",
                    "action": "Network diagnostic attempted",
                    "success": False,
                    "message": (
                        "The automatic network diagnostic could not complete "
                        "the corrective step. A support agent should "
                        "investigate the connection."
                    ),
                }

            # ----------------------------------------------------
            # Linux / macOS
            # ----------------------------------------------------

            before_test = test_internet()

            if before_test["success"]:
                return {
                    "diagnosis": "Network connectivity checked",
                    "action": "Connectivity test completed",
                    "success": False,
                    "message": (
                        "Internet connectivity is currently working. "
                        "No corrective action was required."
                    ),
                }

            return {
                "diagnosis": "Network connectivity issue",
                "action": "Connectivity diagnostic performed",
                "success": False,
                "message": (
                    "Internet connectivity could not be verified. "
                    "Further network investigation is required."
                ),
            }

    # ============================================================
    # SOFTWARE / APPLICATION
    # ============================================================

    if category in {
        "Software & Applications",
        "Application",
    }:

        if any(
            word in text_lower
            for word in [
                "crash",
                "crashing",
                "not responding",
                "application",
                "app",
                "software",
            ]
        ):
            return {
                "diagnosis": "Application/software issue",
                "action": "Application restart recommended",
                "success": False,
                "message": (
                    "The application appears to have a software problem. "
                    "A restart is recommended. Resolve IQ did not force-close "
                    "the application to avoid losing unsaved work."
                ),
            }

    # ============================================================
    # STORAGE / FILES
    # ============================================================

    if category in {
        "Storage & Files",
        "Storage",
    }:

        try:
            total, used, free = shutil.disk_usage("/")

            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            used_percent = (used / total) * 100

            if free_gb < 2:
                return {
                    "diagnosis": "Storage capacity issue",
                    "action": "Storage usage analyzed",
                    "success": False,
                    "message": (
                        f"Only {free_gb:.1f} GB of {total_gb:.1f} GB "
                        f"is available ({used_percent:.0f}% used). "
                        "Automatic file deletion was not performed for "
                        "safety. Manual cleanup is required."
                    ),
                }

            return {
                "diagnosis": "Storage usage checked",
                "action": "Storage usage analyzed",
                "success": False,
                "message": (
                    f"Storage check completed. {free_gb:.1f} GB of free "
                    "space is available. No corrective action was required."
                ),
            }

        except Exception as exc:
            return {
                "diagnosis": "Storage capacity check failed",
                "action": "Storage analysis attempted",
                "success": False,
                "message": (
                    f"Could not analyze storage safely: {exc}"
                ),
            }

    # ============================================================
    # SECURITY
    # ============================================================

    if category in {
        "Security Operations",
        "Security",
    }:

        return {
            "diagnosis": "Potential security incident",
            "action": "No automatic modification performed",
            "success": False,
            "message": (
                "Security issues require human expert review. Resolve IQ "
                "did not modify accounts, passwords, files, or security "
                "settings automatically."
            ),
        }

    # ============================================================
    # ACCOUNT / ACCESS MANAGEMENT
    # ============================================================

    if category in {
        "Account & Access",
        "Access Management",
    }:

        return {
            "diagnosis": "Account/access issue",
            "action": "Account status identified",
            "success": False,
            "message": (
                "The issue appears to involve account access. Password "
                "resets, account unlocking, and permission changes require "
                "authorization and were not performed automatically."
            ),
        }

    # ============================================================
    # DATABASE
    # ============================================================

    if category in {
        "Database & Storage",
        "Database",
    }:

        return {
            "diagnosis": "Database issue",
            "action": "Database modification avoided",
            "success": False,
            "message": (
                "The database issue was identified, but no database "
                "modification was performed automatically. Administrator "
                "review is required."
            ),
        }

    # ============================================================
    # FALLBACK
    # ============================================================

    return {
        "diagnosis": "Issue identified but no safe automatic fix available",
        "action": "Human/support-agent review recommended",
        "success": False,
        "message": (
            "The issue was identified, but no safe automatic remediation "
            "is available for this ticket."
        ),
    }