ROUTING_MAP = {
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