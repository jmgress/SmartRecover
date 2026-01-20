#!/usr/bin/env python3
"""
Mock Data Generator for SmartRecover

This script generates realistic mock data for testing and development by expanding
existing data patterns. It preserves relationships between incidents, tickets, docs,
and change correlations while ensuring unique IDs.

Usage:
    python generate_mock_data.py --scale 10  # Generate 10x the current data
    python generate_mock_data.py --incidents 100 --validate  # Generate 100 incidents with validation
"""

import csv
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys


# Data templates for realistic generation
INCIDENT_TEMPLATES = {
    'titles': [
        'Database connection timeout',
        'API response latency spike',
        'Payment service 500 errors',
        'Memory leak in {} service',
        'SSL certificate expiration warning',
        'Kubernetes cluster node failure',
        'Redis cache connection failures',
        'Elasticsearch indexing delays',
        'CDN cache invalidation stuck',
        'Third-party OAuth provider timeout',
        'Database replica lag critical',
        'Message queue backlog growing',
        'Container registry unavailable',
        'Log aggregation pipeline broken',
        'Rate limiting misconfiguration',
        'Load balancer health check failing',
        'Disk space critical on {} nodes',
        'Network latency to {} region',
        'Service mesh configuration error',
        'Certificate authority unreachable',
    ],
    'services': [
        'auth-service', 'user-service', 'api-gateway', 'order-service',
        'payment-service', 'checkout-service', 'notification-service', 
        'email-service', 'cache-service', 'session-service', 'search-service',
        'product-service', 'cdn', 'frontend', 'oauth-provider', 'database',
        'read-replica', 'reporting-service', 'rabbitmq', 'fulfillment-service',
        'container-registry', 'ci-cd', 'fluentd', 'elasticsearch', 
        'logging-service', 'rate-limiter', 'load-balancer', 'kubernetes',
    ],
    'severities': ['low', 'medium', 'high', 'critical'],
    'statuses': ['open', 'investigating', 'resolved'],
    'teams': [
        'ops-team', 'api-team', 'payments-team', 'platform-team',
        'security-team', 'infra-team', 'search-team', 'identity-team',
        'dba-team', 'devops-team', 'observability-team',
    ],
}

TICKET_TEMPLATES = {
    'resolutions': [
        'Increased connection pool size from {} to {} connections and added exponential backoff retry logic with max 3 attempts. Monitored for 24 hours and confirmed resolution.',
        'Scaled up {} instances from {} to {} pods and optimized query performance by adding database indexes on frequently queried columns. Response times improved from {}s to {}ms average.',
        'Fixed {} timeout by increasing connection timeout to {}s and implementing circuit breaker pattern. Also added health check monitoring.',
        'Rolled back to previous {} version to restore functionality',
        'Implemented {} for automatic failover. Configured {}-node cluster with quorum of {}. Tested failover scenarios successfully.',
        'Promoted replica to primary and rebuilt read replica from backup. Verified data consistency using checksums. Recovery completed within RTO of {} minutes.',
        'Scaled consumer instances and processed backlog within SLA. Increased from {} to {} consumers. Backlog cleared in {} hours.',
        'Restarted {} pods and cleared corrupted cache layer',
        'Renewed SSL certificates and updated load balancer configuration',
        'Manually purged CDN cache and verified asset propagation',
    ],
    'change_descriptions': [
        'Database migration completed last week',
        'Deployed new {} version with performance improvements',
        'Payment provider SDK upgrade deployed yesterday',
        'Added new notification templates last sprint',
        'Automated certificate rotation implementation in progress',
        'Node capacity upgrade scheduled for maintenance window',
        'Redis cluster scaling performed last week',
        'Elasticsearch cluster version upgrade deployed',
        'CDN configuration update for cache TTL',
        'Added backup OAuth provider configuration',
        'Heavy batch job scheduled during peak hours',
        'New order notification feature deployed',
        'Registry storage migration performed',
        'Fluentd configuration update for new log format',
        'Rate limiting threshold adjustment for new API tier',
    ],
    'sources': ['servicenow', 'jira'],
}

DOC_TEMPLATES = {
    'titles': [
        '{} Troubleshooting Guide',
        '{} Service Runbook',
        '{} Performance Tuning',
        '{} Architecture',
        '{} Operations Guide',
        '{} SLA Requirements',
        '{} Configuration Guide',
        '{} Incident Response',
        '{} Monitoring Setup',
        '{} Disaster Recovery',
    ],
    'content_patterns': [
        'Steps: 1. Check {} 2. Verify {} 3. Review recent changes',
        'For {} issues, first check the {} dashboard',
        'Monitor {}, check for {}, review {} settings',
        '{} uses {} that can be intensive. Monitor {} and consider pagination for large batches',
        'For {}: 1. Check {} status 2. Verify {} 3. Review logs',
    ],
}

CHANGE_TEMPLATES = {
    'descriptions': [
        'Database schema update',
        '{} service config update',
        '{} version upgrade',
        '{} SDK upgrade to v{}.{}.{}',
        '{} timeout configuration change',
        '{} template engine update',
        '{} batch processing enhancement',
        'Load balancer {} configuration update',
        '{} node pool scaling automation',
        'Node resource limits adjustment',
        '{} cluster version upgrade to {}.{}',
        '{} connection pool resize',
        '{} mapping template update',
        '{} bulk import job',
        '{} cache TTL configuration change',
        '{} compilation pipeline update',
        '{} client library update',
        '{} rate limiting adjustment',
        '{} storage expansion',
        'Batch reporting job schedule change',
        '{} feature deployment',
        '{} consumer prefetch configuration',
        '{} storage backend migration',
        'CI/CD pipeline image caching update',
        '{} log parsing configuration update',
        '{} index lifecycle policy change',
        '{} threshold adjustment',
        '{} routing rules update',
    ],
}


class MockDataGenerator:
    """Generate realistic mock data with unique IDs and preserved relationships."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with optional random seed for reproducibility."""
        self.seed = seed
        random.seed(seed)
        self.used_incident_ids = set()
        self.used_ticket_ids = set()
        self.used_doc_ids = set()
        self.used_change_ids = set()
        
    def _generate_unique_id(self, prefix: str, used_ids: set, start: int = 1) -> str:
        """Generate a unique ID with the given prefix."""
        counter = start
        while True:
            new_id = f"{prefix}{counter:03d}"
            if new_id not in used_ids:
                used_ids.add(new_id)
                return new_id
            counter += 1
    
    def _random_datetime(self, start_date: datetime, days_range: int) -> datetime:
        """Generate a random datetime within the specified range."""
        return start_date + timedelta(
            days=random.randint(0, days_range),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
    
    def generate_incidents(self, count: int, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Generate realistic incident data."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=14)
        
        incidents = []
        for _ in range(count):
            incident_id = self._generate_unique_id('INC', self.used_incident_ids)
            
            # Select random template and fill in service names if needed
            title_template = random.choice(INCIDENT_TEMPLATES['titles'])
            if '{}' in title_template:
                service = random.choice(INCIDENT_TEMPLATES['services']).replace('-service', '')
                title = title_template.format(service)
            else:
                title = title_template
            
            # Generate description based on title
            description = f"{title} affecting production environment"
            if random.random() > 0.5:
                description += f" with {random.choice(['intermittent', 'consistent', 'sporadic'])} failures"
            
            severity = random.choice(INCIDENT_TEMPLATES['severities'])
            status = random.choice(INCIDENT_TEMPLATES['statuses'])
            
            # Weight status based on severity
            if severity == 'critical' and random.random() > 0.3:
                status = 'resolved' if random.random() > 0.5 else 'investigating'
            
            created_at = self._random_datetime(start_date, 14)
            
            # Add updated_at for resolved incidents
            updated_at = ''
            if status == 'resolved':
                updated_at = (created_at + timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                )).isoformat()
            
            # Select 1-3 affected services
            num_services = random.randint(1, 3)
            affected_services = '|'.join(random.sample(INCIDENT_TEMPLATES['services'], num_services))
            
            assignee = random.choice(INCIDENT_TEMPLATES['teams'])
            
            incidents.append({
                'id': incident_id,
                'title': title,
                'description': description,
                'severity': severity,
                'status': status,
                'created_at': created_at.isoformat(),
                'updated_at': updated_at,
                'affected_services': affected_services,
                'assignee': assignee,
            })
        
        return incidents
    
    def generate_tickets(self, incident_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate ServiceNow tickets for incidents (1-3 per incident)."""
        tickets = []
        
        for incident_id in incident_ids:
            # Generate 1-3 tickets per incident
            num_tickets = random.randint(1, 3)
            
            for i in range(num_tickets):
                ticket_id = self._generate_unique_id(
                    random.choice(['SNOW', 'JIRA-']),
                    self.used_ticket_ids
                )
                
                # First ticket is usually similar_incident, others are related_change
                ticket_type = 'similar_incident' if i == 0 else random.choice(
                    ['similar_incident', 'related_change']
                )
                
                source = 'servicenow' if ticket_id.startswith('SNOW') else 'jira'
                
                resolution = ''
                description = ''
                
                if ticket_type == 'similar_incident':
                    # Generate resolution
                    resolution_template = random.choice(TICKET_TEMPLATES['resolutions'])
                    if '{}' in resolution_template:
                        # Fill in placeholders
                        resolution = resolution_template.format(
                            random.randint(5, 20), random.randint(30, 100),
                            random.randint(2, 10), random.randint(1, 5),
                            random.choice(['Redis', 'service', 'gateway']),
                            random.randint(20, 60)
                        )
                    else:
                        resolution = resolution_template
                    
                    # Add similarity score
                    similarity_score = round(random.uniform(0.65, 0.96), 2)
                else:
                    # Generate change description
                    desc_template = random.choice(TICKET_TEMPLATES['change_descriptions'])
                    if '{}' in desc_template:
                        service = random.choice(INCIDENT_TEMPLATES['services'])
                        description = desc_template.format(service)
                    else:
                        description = desc_template
                    similarity_score = ''
                
                tickets.append({
                    'incident_id': incident_id,
                    'ticket_id': ticket_id,
                    'type': ticket_type,
                    'resolution': resolution,
                    'description': description,
                    'source': source,
                    'similarity_score': similarity_score,
                })
        
        return tickets
    
    def generate_docs(self, incident_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate Confluence docs for incidents (1-2 per incident)."""
        docs = []
        
        for incident_id in incident_ids:
            # Generate 1-2 docs per incident
            num_docs = random.randint(1, 2)
            
            for _ in range(num_docs):
                doc_id = self._generate_unique_id('CONF', self.used_doc_ids)
                
                # Generate title
                title_template = random.choice(DOC_TEMPLATES['titles'])
                service = random.choice(INCIDENT_TEMPLATES['services']).replace('-service', '').title()
                title = title_template.format(service)
                
                # Generate content
                content_template = random.choice(DOC_TEMPLATES['content_patterns'])
                content_parts = [
                    random.choice(['health', 'status', 'configuration', 'logs']),
                    random.choice(['network', 'memory', 'CPU', 'disk']),
                    random.choice(['settings', 'parameters', 'limits']),
                ]
                content = content_template.format(*content_parts)
                
                relevance_score = round(random.uniform(0.70, 0.96), 2)
                
                docs.append({
                    'incident_id': incident_id,
                    'doc_id': doc_id,
                    'title': title,
                    'content': content,
                    'relevance_score': relevance_score,
                })
        
        return docs
    
    def generate_changes(self, incident_ids: List[str], start_date: datetime = None) -> List[Dict[str, Any]]:
        """Generate change correlations for incidents (1-2 per incident)."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=14)
        
        changes = []
        
        for incident_id in incident_ids:
            # Generate 1-2 changes per incident
            num_changes = random.randint(1, 2)
            
            for _ in range(num_changes):
                change_id = self._generate_unique_id('CHG', self.used_change_ids)
                
                # Generate description
                desc_template = random.choice(CHANGE_TEMPLATES['descriptions'])
                if '{}' in desc_template:
                    service = random.choice(INCIDENT_TEMPLATES['services']).replace('-service', '')
                    description = desc_template.format(
                        service,
                        random.randint(1, 5), random.randint(0, 9), random.randint(0, 9)
                    )
                else:
                    description = desc_template
                
                # Generate deployment time (before incident)
                deployed_at = self._random_datetime(start_date - timedelta(days=3), 10)
                
                correlation_score = round(random.uniform(0.45, 0.97), 2)
                
                changes.append({
                    'incident_id': incident_id,
                    'change_id': change_id,
                    'description': description,
                    'deployed_at': deployed_at.isoformat() + 'Z',
                    'correlation_score': correlation_score,
                })
        
        return changes


def save_to_csv(data: List[Dict[str, Any]], filepath: Path, fieldnames: List[str]):
    """Save data to CSV file."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_data(incidents: List[Dict], tickets: List[Dict], 
                  docs: List[Dict], changes: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate generated data for consistency and uniqueness."""
    errors = []
    
    # Check unique IDs
    incident_ids = [inc['id'] for inc in incidents]
    if len(incident_ids) != len(set(incident_ids)):
        errors.append("Duplicate incident IDs found")
    
    ticket_ids = [t['ticket_id'] for t in tickets]
    if len(ticket_ids) != len(set(ticket_ids)):
        errors.append("Duplicate ticket IDs found")
    
    doc_ids = [d['doc_id'] for d in docs]
    if len(doc_ids) != len(set(doc_ids)):
        errors.append("Duplicate doc IDs found")
    
    change_ids = [c['change_id'] for c in changes]
    if len(change_ids) != len(set(change_ids)):
        errors.append("Duplicate change IDs found")
    
    # Check relationships
    incident_id_set = set(incident_ids)
    
    for ticket in tickets:
        if ticket['incident_id'] not in incident_id_set:
            errors.append(f"Ticket {ticket['ticket_id']} references non-existent incident {ticket['incident_id']}")
    
    for doc in docs:
        if doc['incident_id'] not in incident_id_set:
            errors.append(f"Doc {doc['doc_id']} references non-existent incident {doc['incident_id']}")
    
    for change in changes:
        if change['incident_id'] not in incident_id_set:
            errors.append(f"Change {change['change_id']} references non-existent incident {change['incident_id']}")
    
    # Check ticket type consistency
    for ticket in tickets:
        if ticket['type'] == 'similar_incident':
            if not ticket['resolution']:
                errors.append(f"Ticket {ticket['ticket_id']}: similar_incident must have resolution")
        elif ticket['type'] == 'related_change':
            if not ticket['description']:
                errors.append(f"Ticket {ticket['ticket_id']}: related_change must have description")
    
    return len(errors) == 0, errors


def main():
    """Main function to generate mock data."""
    parser = argparse.ArgumentParser(
        description='Generate realistic mock data for SmartRecover',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate 10x the current data (150 incidents):
    %(prog)s --scale 10

  Generate specific number of incidents:
    %(prog)s --incidents 200

  Generate with validation and custom seed:
    %(prog)s --scale 5 --validate --seed 123
        """
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=None,
        help='Scale factor for data generation (e.g., 10 for 10x current data of 15 incidents)'
    )
    parser.add_argument(
        '--incidents',
        type=int,
        default=None,
        help='Explicit number of incidents to generate'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate generated data before saving'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory for CSV files (default: backend/data/csv/)'
    )
    parser.add_argument(
        '--preserve-existing',
        action='store_true',
        help='Preserve existing data and only append new data (maintains test compatibility)'
    )
    
    args = parser.parse_args()
    
    # Determine number of incidents to generate
    if args.incidents:
        num_incidents = args.incidents
    elif args.scale:
        num_incidents = 15 * args.scale  # Current base is 15 incidents
    else:
        parser.error("Either --scale or --incidents must be specified")
    
    # Set output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        script_dir = Path(__file__).parent
        output_dir = script_dir / 'csv'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating mock data with seed {args.seed}...")
    print(f"Target: {num_incidents} incidents")
    
    # Generate data
    generator = MockDataGenerator(seed=args.seed)
    
    # Load existing data if preserving
    existing_incidents = []
    existing_tickets = []
    existing_docs = []
    existing_changes = []
    
    if args.preserve_existing and output_dir.exists():
        print("\nLoading existing data to preserve...")
        try:
            # Load existing incidents
            inc_path = output_dir / 'incidents.csv'
            if inc_path.exists():
                with open(inc_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_incidents = list(reader)
                    # Track existing IDs
                    for inc in existing_incidents:
                        generator.used_incident_ids.add(inc['id'])
                print(f"  - Loaded {len(existing_incidents)} existing incidents")
            
            # Load existing tickets
            tick_path = output_dir / 'servicenow_tickets.csv'
            if tick_path.exists():
                with open(tick_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_tickets = list(reader)
                    for tick in existing_tickets:
                        generator.used_ticket_ids.add(tick['ticket_id'])
                print(f"  - Loaded {len(existing_tickets)} existing tickets")
            
            # Load existing docs
            docs_path = output_dir / 'confluence_docs.csv'
            if docs_path.exists():
                with open(docs_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_docs = list(reader)
                    for doc in existing_docs:
                        generator.used_doc_ids.add(doc['doc_id'])
                print(f"  - Loaded {len(existing_docs)} existing docs")
            
            # Load existing changes
            changes_path = output_dir / 'change_correlations.csv'
            if changes_path.exists():
                with open(changes_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_changes = list(reader)
                    for change in existing_changes:
                        generator.used_change_ids.add(change['change_id'])
                print(f"  - Loaded {len(existing_changes)} existing changes")
            
            # Adjust target to only generate additional data
            existing_count = len(existing_incidents)
            num_incidents = max(0, num_incidents - existing_count)
            print(f"\nGenerating {num_incidents} additional incidents to reach target...")
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")
            print("Generating all data from scratch...")
    
    print("Generating incidents...")
    new_incidents = generator.generate_incidents(num_incidents) if num_incidents > 0 else []
    incidents = existing_incidents + [dict(inc) for inc in new_incidents]
    new_incident_ids = [inc['id'] for inc in new_incidents]
    
    print(f"Generating tickets for {len(new_incident_ids)} new incidents...")
    new_tickets = generator.generate_tickets(new_incident_ids) if new_incident_ids else []
    tickets = existing_tickets + new_tickets
    
    print(f"Generating documentation for {len(new_incident_ids)} new incidents...")
    new_docs = generator.generate_docs(new_incident_ids) if new_incident_ids else []
    docs = existing_docs + new_docs
    
    print(f"Generating change correlations for {len(new_incident_ids)} new incidents...")
    new_changes = generator.generate_changes(new_incident_ids) if new_incident_ids else []
    changes = existing_changes + new_changes
    
    print(f"\nGenerated:")
    print(f"  - {len(incidents)} incidents")
    print(f"  - {len(tickets)} tickets")
    print(f"  - {len(docs)} documentation entries")
    print(f"  - {len(changes)} change correlations")
    
    # Validate if requested
    if args.validate:
        print("\nValidating data...")
        is_valid, errors = validate_data(incidents, tickets, docs, changes)
        if not is_valid:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        print("✅ Validation passed")
    
    # Save to CSV files
    print(f"\nSaving to {output_dir}...")
    
    save_to_csv(
        incidents,
        output_dir / 'incidents.csv',
        ['id', 'title', 'description', 'severity', 'status', 'created_at', 
         'updated_at', 'affected_services', 'assignee']
    )
    
    save_to_csv(
        tickets,
        output_dir / 'servicenow_tickets.csv',
        ['incident_id', 'ticket_id', 'type', 'resolution', 'description', 
         'source', 'similarity_score']
    )
    
    save_to_csv(
        docs,
        output_dir / 'confluence_docs.csv',
        ['incident_id', 'doc_id', 'title', 'content', 'relevance_score']
    )
    
    save_to_csv(
        changes,
        output_dir / 'change_correlations.csv',
        ['incident_id', 'change_id', 'description', 'deployed_at', 'correlation_score']
    )
    
    print("✅ Mock data generation complete!")
    print(f"\nCSV files saved to: {output_dir}")


if __name__ == '__main__':
    main()
