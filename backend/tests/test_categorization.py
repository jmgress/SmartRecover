"""Tests for canonical incident categorization."""

import pytest

from backend.utils.categorization import DEFAULT_CATEGORY, categorize_incident


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
