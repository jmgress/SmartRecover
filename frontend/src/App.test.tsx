import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { useIncidents } from './hooks/useIncidents';

jest.mock('./hooks/useIncidents');

describe('App', () => {
  it('renders loading state', () => {
    (useIncidents as jest.Mock).mockReturnValue({
      incidents: [],
      loading: true,
      error: null,
    });

    render(<App />);
    expect(screen.getByText('Loading incidents...')).toBeInTheDocument();
  });

  it('renders sidebar and main content when loaded', () => {
    const mockIncidents = [
      {
        id: 'INC001',
        title: 'Test Incident',
        description: 'Test',
        severity: 'high',
        status: 'open',
        created_at: '2024-01-01T00:00:00Z',
        affected_services: [],
      },
    ];

    (useIncidents as jest.Mock).mockReturnValue({
      incidents: mockIncidents,
      loading: false,
      error: null,
    });

    render(<App />);
    expect(screen.getByText('Incidents')).toBeInTheDocument();
    expect(screen.getByText('Select an incident to begin')).toBeInTheDocument();
  });
});
