from typing import Final
import re

from backend.utils.logger import get_logger

logger = get_logger(__name__)


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


_EXTERNAL_ALIASES = {
    **{category.lower(): category for category in CATEGORIES},
    "software": "Application",
    "hardware": "Infrastructure",
    "server": "Infrastructure",
    "operating system": "Infrastructure",
    "database": "Database",
    "db": "Database",
    "sql": "Database",
    "email": "Application",
    "authentication": "Security",
    "certificate": "Security",
    "disk": "Storage",
    "logging": "Monitoring",
    "redis": "Cache",
    "cdn": "Cache",
    "payment": "Payments",
}


def _external_category(value: str) -> str | None:
    key = re.sub(r"[_\s-]+", " ", value.strip().lower())
    return _EXTERNAL_ALIASES.get(key)


def categorize_servicenow(
    category: str, subcategory: str, title: str, description: str = ""
) -> str:
    """Prefer a recognized specific subcategory over the broader category."""
    for value in (subcategory, category):
        mapped = _external_category(value)
        if mapped:
            return mapped
    logger.warning("ServiceNow category metadata unmapped; using incident text fallback")
    return categorize_incident(title, description)


def categorize_jira(
    issue_type: str, components: list[str], title: str, description: str = ""
) -> str:
    """Use unambiguous components, then issue type, then the legacy text fallback."""
    mapped = {category for name in components if (category := _external_category(name))}
    if len(mapped) == 1:
        return mapped.pop()
    if len(mapped) > 1:
        logger.warning("Conflicting Jira component categories; using issue type or text fallback")
    category = _external_category(issue_type)
    if category:
        return category
    logger.warning("Jira category metadata unmapped; using incident text fallback")
    return categorize_incident(title, description)
