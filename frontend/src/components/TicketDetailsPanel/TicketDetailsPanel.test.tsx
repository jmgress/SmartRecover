import React from 'react';
import { render, screen } from '@testing-library/react';
import { TicketDetailsPanel } from './TicketDetailsPanel';

describe('TicketDetailsPanel', () => {
  it('shows source attribution for Splunk incidents', () => {
    render(
      <TicketDetailsPanel
        loading={false}
        ticketDetails={{
          incident: {
            id: 'SPL-1001',
            title: 'API latency spike',
            description: 'High latency detected in checkout API',
            severity: 'high',
            status: 'open',
            created_at: '2026-08-12T20:00:00Z',
            updated_at: '2026-08-12T20:15:00Z',
            affected_services: ['checkout-api'],
            assignee: 'sre-oncall',
            source: 'splunk',
          },
          agent_results: null,
        }}
      />
    );

    expect(screen.getByText('Source:')).toBeInTheDocument();
    expect(screen.getByText('splunk')).toBeInTheDocument();
  });
});
