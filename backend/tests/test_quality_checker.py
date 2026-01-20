"""
Tests for ServiceNow ticket quality checker.
"""
import pytest
from backend.utils.quality_checker import (
    calculate_ticket_quality,
    calculate_tickets_quality,
    assess_similar_incidents_quality,
    QualityLevel
)


class TestCalculateTicketQuality:
    """Test individual ticket quality calculation."""
    
    def test_good_quality_ticket(self):
        """Test ticket with good quality (complete description and resolution)."""
        ticket = {
            'ticket_id': 'SNOW001',
            'description': 'Database connection timeouts were occurring due to exhausted connection pool. Analysis showed peak load exceeded configured limit.',
            'resolution': 'Increased connection pool size from 10 to 50 connections and added exponential backoff retry logic with max 3 attempts. Monitored for 24 hours and confirmed resolution.'
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 1.0
        assert result['level'] == QualityLevel.GOOD
        assert len(result['issues']) == 0
        assert result['details']['description_score'] == 0.5
        assert result['details']['resolution_score'] == 0.5
    
    def test_warning_quality_ticket_short_fields(self):
        """Test ticket with warning quality (short description and resolution)."""
        ticket = {
            'ticket_id': 'SNOW002',
            'description': 'Short description here',
            'resolution': 'Quick fix applied ok'
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 0.7  # 0.35 + 0.35
        assert result['level'] == QualityLevel.WARNING
        assert len(result['issues']) == 0  # No issues, just not optimal
        assert result['details']['description_score'] == 0.35
        assert result['details']['resolution_score'] == 0.35
    
    def test_poor_quality_ticket_missing_resolution(self):
        """Test ticket with poor quality (missing resolution)."""
        ticket = {
            'ticket_id': 'SNOW003',
            'description': 'Very short',
            'resolution': ''
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 0.25
        assert result['level'] == QualityLevel.POOR
        assert "Missing resolution" in result['issues']
        assert any("Description too short" in issue for issue in result['issues'])
        assert result['details']['description_score'] == 0.25
        assert result['details']['resolution_score'] == 0.0
    
    def test_poor_quality_ticket_missing_both(self):
        """Test ticket with poor quality (missing both fields)."""
        ticket = {
            'ticket_id': 'SNOW004',
            'description': '',
            'resolution': ''
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 0.0
        assert result['level'] == QualityLevel.POOR
        assert "Missing description" in result['issues']
        assert "Missing resolution" in result['issues']
        assert result['details']['description_score'] == 0.0
        assert result['details']['resolution_score'] == 0.0
    
    def test_ticket_with_no_fields(self):
        """Test ticket with no description or resolution fields."""
        ticket = {
            'ticket_id': 'SNOW005',
            'type': 'related_change'
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 0.0
        assert result['level'] == QualityLevel.POOR
        assert "Missing description" in result['issues']
        assert "Missing resolution" in result['issues']
    
    def test_ticket_with_whitespace_only(self):
        """Test ticket with whitespace-only fields."""
        ticket = {
            'ticket_id': 'SNOW006',
            'description': '   ',
            'resolution': '   '
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['score'] == 0.0
        assert result['level'] == QualityLevel.POOR
        assert "Missing description" in result['issues']
        assert "Missing resolution" in result['issues']
    
    def test_boundary_20_chars_description(self):
        """Test ticket with exactly 20 character description."""
        ticket = {
            'ticket_id': 'SNOW007',
            'description': '12345678901234567890',  # Exactly 20 chars
            'resolution': 'Good resolution with enough detail to be considered complete and helpful'
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['details']['description_score'] == 0.35
        assert result['details']['resolution_score'] == 0.5
        assert result['score'] == 0.85
        assert result['level'] == QualityLevel.GOOD
    
    def test_boundary_50_chars_description(self):
        """Test ticket with exactly 50 character description."""
        ticket = {
            'ticket_id': 'SNOW008',
            'description': '12345678901234567890123456789012345678901234567890',  # Exactly 50 chars
            'resolution': 'Good resolution with enough detail to be considered complete and helpful'
        }
        
        result = calculate_ticket_quality(ticket)
        
        assert result['details']['description_score'] == 0.5
        assert result['details']['resolution_score'] == 0.5
        assert result['score'] == 1.0
        assert result['level'] == QualityLevel.GOOD


class TestCalculateTicketsQuality:
    """Test aggregate ticket quality calculation."""
    
    def test_empty_list(self):
        """Test with empty ticket list."""
        result = calculate_tickets_quality([])
        
        assert result['average_score'] == 0.0
        assert result['overall_level'] == QualityLevel.POOR
        assert result['ticket_qualities'] == []
        assert result['summary']['total_tickets'] == 0
        assert result['summary']['good_count'] == 0
        assert result['summary']['warning_count'] == 0
        assert result['summary']['poor_count'] == 0
    
    def test_all_good_quality_tickets(self):
        """Test with all good quality tickets."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'type': 'similar_incident',
                'description': 'Database connection timeouts due to exhausted connection pool',
                'resolution': 'Increased connection pool size from 10 to 50 connections and added retry logic'
            },
            {
                'ticket_id': 'SNOW002',
                'type': 'similar_incident',
                'description': 'API gateway experiencing high latency during peak hours',
                'resolution': 'Scaled up instances from 3 to 8 pods and optimized query performance'
            }
        ]
        
        result = calculate_tickets_quality(tickets)
        
        assert result['average_score'] == 1.0
        assert result['overall_level'] == QualityLevel.GOOD
        assert len(result['ticket_qualities']) == 2
        assert result['summary']['total_tickets'] == 2
        assert result['summary']['good_count'] == 2
        assert result['summary']['warning_count'] == 0
        assert result['summary']['poor_count'] == 0
    
    def test_mixed_quality_tickets(self):
        """Test with mixed quality tickets."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'description': 'Database connection timeouts due to exhausted connection pool',
                'resolution': 'Increased connection pool size from 10 to 50 connections and added retry logic'
            },
            {
                'ticket_id': 'SNOW002',
                'description': 'Short desc',
                'resolution': 'Fix applied'
            },
            {
                'ticket_id': 'SNOW003',
                'description': '',
                'resolution': ''
            }
        ]
        
        result = calculate_tickets_quality(tickets)
        
        # Average: (1.0 + 0.5 + 0.0) / 3 = 0.5
        assert result['average_score'] == 0.5
        assert result['overall_level'] == QualityLevel.WARNING
        assert len(result['ticket_qualities']) == 3
        assert result['summary']['total_tickets'] == 3
        assert result['summary']['good_count'] == 1
        assert result['summary']['warning_count'] == 1
        assert result['summary']['poor_count'] == 1
    
    def test_all_poor_quality_tickets(self):
        """Test with all poor quality tickets."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'description': '',
                'resolution': ''
            },
            {
                'ticket_id': 'SNOW002',
                'description': 'Short',
                'resolution': 'Fix'
            }
        ]
        
        result = calculate_tickets_quality(tickets)
        
        # Both should be poor quality (score 0.0 and 0.25)
        # Average: (0.0 + 0.25) / 2 = 0.125
        assert result['average_score'] < 0.5
        assert result['overall_level'] == QualityLevel.POOR
        assert len(result['ticket_qualities']) == 2
        # First ticket: 0 score = poor, Second ticket: 0.25 score = poor
        assert result['summary']['poor_count'] >= 1
    
    def test_ticket_quality_includes_identifiers(self):
        """Test that individual ticket qualities include ticket_id and type."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'type': 'similar_incident',
                'description': 'Database connection timeouts due to exhausted connection pool',
                'resolution': 'Increased connection pool size and added retry logic'
            }
        ]
        
        result = calculate_tickets_quality(tickets)
        
        assert len(result['ticket_qualities']) == 1
        quality = result['ticket_qualities'][0]
        assert quality['ticket_id'] == 'SNOW001'
        assert quality['ticket_type'] == 'similar_incident'
        assert quality['score'] == 1.0
        assert quality['level'] == QualityLevel.GOOD


class TestAssessSimilarIncidentsQuality:
    """Test similar incidents quality assessment."""
    
    def test_filters_similar_incidents_only(self):
        """Test that it only assesses similar_incident type tickets."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'type': 'similar_incident',
                'description': 'Database connection timeouts due to exhausted connection pool',
                'resolution': 'Increased connection pool size and added retry logic'
            },
            {
                'ticket_id': 'SNOW002',
                'type': 'related_change',
                'description': 'Database migration completed last week',
                'resolution': ''
            }
        ]
        
        result = assess_similar_incidents_quality(tickets)
        
        # Should only assess the similar_incident, not the related_change
        assert result['summary']['total_tickets'] == 1
        assert result['ticket_qualities'][0]['ticket_id'] == 'SNOW001'
    
    def test_empty_after_filtering(self):
        """Test with no similar_incident type tickets."""
        tickets = [
            {
                'ticket_id': 'SNOW001',
                'type': 'related_change',
                'description': 'Some change',
                'resolution': ''
            }
        ]
        
        result = assess_similar_incidents_quality(tickets)
        
        assert result['summary']['total_tickets'] == 0
        assert result['overall_level'] == QualityLevel.POOR
