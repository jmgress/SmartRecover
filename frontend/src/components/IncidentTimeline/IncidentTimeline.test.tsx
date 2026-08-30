import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IncidentTimeline } from './IncidentTimeline';
import { AgentResults, Incident } from '../../types/incident';

const incident: Incident = {
  id: 'INC001',
  title: 'Database connection pool exhausted',
  description: 'Connections are timing out',
  severity: 'high',
  status: 'resolved',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T12:00:00Z',
  affected_services: ['database'],
};

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
};

describe('IncidentTimeline', () => {
  it('renders incident creation, update, and correlated change events in order', () => {
    render(<IncidentTimeline incident={incident} agentResults={agentResults} />);

    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('Change deployed: CHG001');
    expect(items[1]).toHaveTextContent('Incident created');
    expect(items[2]).toHaveTextContent('Status updated to resolved');
  });

  it('exposes timeline items as keyboard-focusable, accessible list entries', async () => {
    render(<IncidentTimeline incident={incident} agentResults={agentResults} />);

    const list = screen.getByRole('list', { name: /incident timeline/i });
    expect(list).toBeInTheDocument();

    const items = screen.getAllByRole('listitem');
    items.forEach((item) => expect(item).toHaveAttribute('tabindex', '0'));

    await userEvent.tab();
    expect(items[0]).toHaveFocus();
  });
});
