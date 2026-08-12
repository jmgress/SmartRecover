import React from 'react';
import { render, screen } from '@testing-library/react';
import { IncidentItem } from './IncidentItem';

describe('IncidentItem', () => {
  it('renders the incident source when provided', () => {
    render(
      <IncidentItem
        incident={{
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
        }}
        isActive={false}
        onClick={jest.fn()}
      />
    );

    expect(screen.getByText('Source: splunk')).toBeInTheDocument();
  });
});
