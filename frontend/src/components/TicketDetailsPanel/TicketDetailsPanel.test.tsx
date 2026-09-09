import React from 'react';
import { render, screen } from '@testing-library/react';
import { TicketDetailsPanel } from './TicketDetailsPanel';

jest.mock('./AgentResultsTabs', () => ({
  AgentResultsTabs: () => <div>Agent Results</div>,
}));

jest.mock('./SuggestedFixCard', () => ({
  SuggestedFixCard: () => <div>Suggested Fix</div>,
}));

jest.mock('./ResolutionFeedback', () => ({
  ResolutionFeedback: () => <div>Resolution Feedback</div>,
}));

jest.mock('../StatusDropdown', () => ({
  StatusDropdown: () => <div>Status Dropdown</div>,
}));

jest.mock('../IncidentTimeline', () => ({
  IncidentTimeline: () => <div>Timeline</div>,
}));

describe('TicketDetailsPanel', () => {
  it('shows the automation badge and decision reason when present', () => {
    render(
      <TicketDetailsPanel
        loading={false}
        ticketDetails={{
          incident: {
            id: 'INC009',
            title: 'Database replica lag critical',
            description: 'Replica lag in production',
            severity: 'medium',
            status: 'open',
            category: 'Database',
            created_at: '2026-01-19T04:51:56.376226Z',
            affected_services: ['api-gateway'],
          },
          agent_results: {
            suggested_fix: {
              id: 'rem-db-001',
              title: 'Restart Database Connection Pool',
              description: 'Restart the pool',
              script: 'kubectl rollout restart deployment/db-connection-pool',
              risk_level: 'low',
              estimated_duration: '2 minutes',
              prerequisites: [],
              confidence_score: 0.85,
              rationale: 'Highest-confidence remediation',
              source: 'remediation_engine',
            },
            automation_decision: {
              automated: true,
              reason: 'auto-remediation simulated and audited',
              category: 'Database',
              threshold: 0.6,
              incident_confidence: 0.7,
              suggested_fix_confidence: 0.85,
              risk_level: 'low',
              severity: 'medium',
              suggested_fix_id: 'rem-db-001',
              audit_record_id: 'audit-1',
            },
          },
        }}
      />
    );

    expect(screen.getByText('Auto-remediated')).toBeInTheDocument();
    expect(screen.getByText('Auto-remediation approved')).toBeInTheDocument();
    expect(screen.getByText('auto-remediation simulated and audited')).toBeInTheDocument();
    expect(screen.getAllByText('Database').length).toBeGreaterThan(0);
  });
});
