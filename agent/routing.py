ROUTING_MAP = {
    # Enterprise Taxonomies
    "Network & Connectivity": "Network Support",
    "Account & Access": "Identity & Access Management",
    "Email & Collaboration": "Collaboration Support",
    "Software & Applications": "Application Support",
    "Infrastructure & Servers": "Infrastructure Support",
    "Database & Storage": "Database Operations",
    "Hardware & Peripherals": "End-User Computing",
    "Security Operations": "Security Operations",
    "Storage & Files": "Infrastructure Support",

    # Legacy Category Support
    "Network": "Network Support",
    "Infrastructure": "Infrastructure Support",
    "Application": "Application Support",
    "Security": "Security Operations",
    "Database": "Database Administration",
    "Storage": "Storage & Infrastructure Support",
    "Access Management": "Identity & Access Management",
}


def route(category: str):
    """Map a predicted category to the responsible department."""

    from .models import RoutingResult

    department = ROUTING_MAP.get(
        category,
        "General IT Support"
    )

    return RoutingResult(department=department)