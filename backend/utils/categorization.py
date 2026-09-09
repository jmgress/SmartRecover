from typing import Final


CATEGORIES: Final[tuple[str, ...]] = (
    "Database",
    "Application",
    "Infrastructure",
    "Network",
    "Security",
    "Storage",
    "Monitoring",
    "Cache",
    "Payments",
    "API",
)
DEFAULT_CATEGORY: Final[str] = "Application"
CATEGORY_RULES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Database", ("database", "replica lag", "connection timeout")),
    ("Application", ("memory leak",)),
    ("Infrastructure", ("kubernetes", "container", "load balancer", "service mesh")),
    ("Network", ("network", "latency")),
    ("Security", ("ssl", "certificate", "oauth")),
    ("Storage", ("disk", "storage")),
    ("Monitoring", ("log", "elasticsearch")),
    ("Cache", ("cache", "redis", "cdn")),
    ("Payments", ("payment",)),
    ("API", ("api",)),
)


def categorize_incident(title: str, description: str = "") -> str:
    """Infer the canonical category for an incident from its title and description."""
    haystack = f"{title or ''} {description or ''}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return DEFAULT_CATEGORY
