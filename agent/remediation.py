"""
Safe automated remediation actions.

The system attempts simple, low-risk fixes for common IT issues.
High-risk actions such as password changes, account changes,
database modifications, or security actions are not performed automatically.
"""

import subprocess
import platform
import shutil


def run_command(command, timeout=15):
    """Run a system command safely and return the result."""

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

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
        }


def test_internet():
    """Test whether the machine can reach the internet."""

    system = platform.system()

    if system == "Windows":
        command = ["ping", "-n", "1", "8.8.8.8"]
    else:
        command = ["ping", "-c", "1", "8.8.8.8"]

    return run_command(command, timeout=10)


def diagnose_and_fix(category: str, text: str):
    """
    Diagnose the ticket and attempt a safe automated fix.

    Returns:
        dict containing:
        - diagnosis
        - action
        - success
        - message
    """

    text_lower = text.lower()

    # ============================================================
    # NETWORK / WIFI
    # ============================================================

    if category == "Network":

        # --------------------------------------------------------
        # Wi-Fi / Internet / Connectivity
        # --------------------------------------------------------

        if any(word in text_lower for word in [
            "wifi",
            "wi-fi",
            "internet",
            "connection",
            "connectivity",
            "network",
        ]):

            system = platform.system()

            # Windows
            if system == "Windows":

                # Step 1: Check current connectivity
                before_test = test_internet()

                if before_test["success"]:
                    return {
                        "diagnosis": "Network connectivity issue",
                        "action": "Connectivity tested",
                        "success": True,
                        "message": (
                            "Your computer already has internet connectivity. "
                            "The network appears to be working."
                        ),
                    }

                # Step 2: Flush DNS cache
                dns_result = run_command(
                    ["ipconfig", "/flushdns"],
                    timeout=10,
                )

                # Step 3: Test connectivity again
                after_test = test_internet()

                if after_test["success"]:
                    return {
                        "diagnosis": "Network/DNS connectivity issue",
                        "action": "DNS cache cleared and connection restored",
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
                            "connectivity is still unavailable. "
                            "Further network investigation is required."
                        ),
                    }

                return {
                    "diagnosis": "Network connectivity issue",
                    "action": "Network diagnostic attempted",
                    "success": False,
                    "message": (
                        "The automatic network fix could not be completed. "
                        "A support agent should investigate the connection."
                    ),
                }

            # Linux / macOS
            else:

                before_test = test_internet()

                if before_test["success"]:
                    return {
                        "diagnosis": "Network connectivity issue",
                        "action": "Connectivity tested",
                        "success": True,
                        "message": (
                            "Your computer already has internet connectivity."
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

        # --------------------------------------------------------
        # VPN
        # --------------------------------------------------------

        if "vpn" in text_lower:

            return {
                "diagnosis": "VPN connectivity issue",
                "action": "VPN connection requires verification",
                "success": False,
                "message": (
                    "The system identified a VPN issue, but VPN credentials "
                    "and corporate VPN configuration cannot be modified "
                    "automatically. Please reconnect to the company VPN "
                    "or escalate to Network Support."
                ),
            }

    # ============================================================
    # APPLICATION / SOFTWARE
    # ============================================================

    if category == "Application":

        if any(word in text_lower for word in [
            "crash",
            "crashing",
            "not responding",
            "application",
            "app",
            "software",
        ]):

            return {
                "diagnosis": "Application/software issue",
                "action": "Application restart recommended",
                "success": False,
                "message": (
                    "The application appears to have a software problem. "
                    "A restart is recommended. The AI did not force-close "
                    "the application to avoid losing unsaved work."
                ),
            }

    # ============================================================
    # STORAGE
    # ============================================================

    if category == "Storage":

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
                        "Automatic file deletion was not performed "
                        "for safety. Manual cleanup is required."
                    ),
                }

            return {
                "diagnosis": "Storage issue",
                "action": "Storage usage analyzed",
                "success": True,
                "message": (
                    f"Storage check completed. "
                    f"{free_gb:.1f} GB of free space is available."
                ),
            }

        except Exception as e:

            return {
                "diagnosis": "Storage capacity issue",
                "action": "Storage analysis attempted",
                "success": False,
                "message": f"Could not analyze storage: {e}",
            }

    # ============================================================
    # SECURITY
    # ============================================================

    if category == "Security":

        return {
            "diagnosis": "Potential security incident",
            "action": "No automatic modification performed",
            "success": False,
            "message": (
                "Security issues require human expert review. "
                "The system did not modify accounts, passwords, "
                "files, or security settings automatically."
            ),
        }

    # ============================================================
    # ACCESS MANAGEMENT
    # ============================================================

    if category == "Access Management":

        return {
            "diagnosis": "Account/access issue",
            "action": "Account status identified",
            "success": False,
            "message": (
                "The issue appears to involve account access. "
                "Password resets, account unlocking, and permission "
                "changes require authorization and were not performed "
                "automatically."
            ),
        }

    # ============================================================
    # DATABASE
    # ============================================================

    if category == "Database":

        return {
            "diagnosis": "Database connectivity issue",
            "action": "Database modification avoided",
            "success": False,
            "message": (
                "The database issue was identified, but no database "
                "modification was performed automatically. "
                "Administrator review is required."
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