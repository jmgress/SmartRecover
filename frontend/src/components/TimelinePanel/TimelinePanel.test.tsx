import React from 'react';
import { render, screen } from '@testing-library/react';
import { TimelinePanel } from './TimelinePanel';
import { TicketDetails } from '../../types/incident';

jest.mock('../IncidentTimeline', () => ({
  IncidentTimeline: () => <div>Timeline events</div>,
}));

const ticketDetails: TicketDetails = {
  incident: {
    id: 'INC001',
    title: 'Test Incident',
    description: 'Test',
    severity: 'high',
    status: 'open',
    created_at: '2024-01-01T00:00:00Z',
    affected_services: [],
  },
  agent_results: null,
};

describe('TimelinePanel', () => {
  it('shows an empty state when no incident is selected', () => {
    render(<TimelinePanel ticketDetails={null} />);
    expect(screen.getByText('Select an incident to view its timeline')).toBeInTheDocument();
  });

  it('renders the timeline for a selected incident', () => {
    render(<TimelinePanel ticketDetails={ticketDetails} />);
    expect(screen.getByRole('heading', { name: 'Timeline' })).toBeInTheDocument();
    expect(screen.getByText('Timeline events')).toBeInTheDocument();
  });
});
