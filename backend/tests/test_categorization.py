"""Tests for canonical incident categorization."""

import pytest

from backend.utils.categorization import (
    CATEGORIES, DEFAULT_CATEGORY, categorize_incident, categorize_jira, categorize_servicenow,
)


@pytest.mark.parametrize(
    ("title", "description", "expected_category"),
    [
        ("Database connection timeout", "Read queries are failing", "Database"),
        ("Memory leak in auth service", "Production pods keep growing", "Application"),
        ("Kubernetes cluster node failure", "Container restarts continue", "Infrastructure"),
        ("Network latency to us-east region", "Cross-region traffic is slow", "Network"),
        ("SSL certificate expiration warning", "OAuth login is impacted", "Security"),
        ("Disk space critical on cache nodes", "Storage pool nearing capacity", "Storage"),
        ("Log aggregation pipeline broken", "Elasticsearch indexing is delayed", "Monitoring"),
        ("Redis cache connection failures", "CDN invalidation is stuck", "Cache"),
        ("Payment service 500 errors", "Checkout retries are spiking", "Payments"),
        ("API authentication failures", "Customer-facing endpoints are returning 401s", "API"),
    ],
)
def test_categorize_incident_matches_expected_keywords(
    title: str,
    description: str,
    expected_category: str,
):
    """Each canonical category should match at least one representative keyword."""
    assert categorize_incident(title, description) == expected_category


def test_categorize_incident_defaults_to_application():
    """Incidents without a matching keyword should use the Application default."""
    assert categorize_incident("Unexpected user report", "Symptom is still under investigation") == DEFAULT_CATEGORY


@pytest.mark.parametrize("category", CATEGORIES)
def test_external_metadata_accepts_every_canonical_category(category):
    assert categorize_servicenow(category.upper(), "", "Payment failure") == category
    assert categorize_jira("Incident", [f" {category.upper()} "], "Payment failure") == category


@pytest.mark.parametrize(
    ("category", "subcategory", "title", "expected"),
    [
        ("software", "database", "Payment failure", "Database"),
        ("hardware", "unrecognized", "API failure", "Infrastructure"),
        ("software", "operating_system", "API failure", "Infrastructure"),
        ("unknown", "", "Redis timeout", "Cache"),
        ("", "", "Unexpected symptom", "Application"),
        ("Network", "Security", "Payment failure", "Security"),
    ],
)
def test_servicenow_category_precedence_and_fallback(category, subcategory, title, expected):
    assert categorize_servicenow(category, subcategory, title) == expected


@pytest.mark.parametrize(
    ("issue_type", "components", "title", "expected"),
    [
        ("Incident", ["unknown", "redis"], "Payment failure", "Cache"),
        ("Security", ["redis", "Cache"], "Payment failure", "Cache"),
        ("Security", ["Network", "Database"], "Payment failure", "Security"),
        ("Incident", ["Network", "Database"], "Payment failure", "Payments"),
        ("Incident", ["Database", "Network"], "Payment failure", "Payments"),
        ("API", [], "Payment failure", "API"),
        ("Incident", [], "Unexpected symptom", "Application"),
        ("Incident", ["payments-team"], "Disk full", "Storage"),
    ],
)
def test_jira_category_precedence_and_fallback(issue_type, components, title, expected):
    assert categorize_jira(issue_type, components, title) == expected
