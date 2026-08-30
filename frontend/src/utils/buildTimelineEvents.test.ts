import { buildTimelineEvents } from './buildTimelineEvents';
import { AgentResults, Incident } from '../types/incident';

const incident: Incident = {
  id: 'INC001',
  title: 'Database connection pool exhausted',
  description: 'Connections are timing out',
  severity: 'high',
  status: 'in_progress',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T12:00:00Z',
  affected_services: ['database'],
};

describe('buildTimelineEvents', () => {
  it('includes an incident_created event when agentResults is null', () => {
    const events = buildTimelineEvents(incident, null);

    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({ type: 'incident_created', title: 'Incident created' });
    expect(events[1]).toMatchObject({ type: 'incident_updated' });
  });

  it('merges correlated changes, events, and the suggested fix in chronological order', () => {
    const agentResults: AgentResults = {
      change_results: {
        source: 'change_correlation',
        incident_id: 'INC001',
        high_correlation_changes: [],
        medium_correlation_changes: [],
        all_correlations: [
          {
            change_id: 'CHG001',
            description: 'Deployed new connection pool config',
            deployed_at: '2024-01-01T09:00:00Z',
            correlation_score: 0.9,
          },
        ],
        top_suspect: null,
      },
      events_results: {
        source: 'events',
        incident_id: 'INC001',
        events: [
          {
            id: 'EVT001',
            timestamp: '2024-01-01T11:00:00Z',
            type: 'error_spike',
            severity: 'CRITICAL',
            application: 'db-service',
            message: 'Spike in connection errors',
          },
        ],
        total_count: 1,
        critical_count: 1,
        warning_count: 0,
      },
      suggested_fix: {
        id: 'rem-001',
        title: 'Restart connection pool',
        description: 'Restart the pool',
        script: 'kubectl rollout restart deployment/db-pool',
        risk_level: 'low',
        estimated_duration: '2 min',
        prerequisites: [],
        confidence_score: 0.9,
        rationale: 'Highest-confidence remediation',
        source: 'remediation_engine',
      },
    };

    const events = buildTimelineEvents(incident, agentResults);

    expect(events.map((e) => e.type)).toEqual([
      'change',
      'incident_created',
      'event',
      'incident_updated',
      'resolution',
    ]);
  });
});
