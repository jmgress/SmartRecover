import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StatusDropdown } from './StatusDropdown';
import { Incident } from '../../types/incident';

const mockUpdateStatus = jest.fn();

jest.mock('../../hooks/useUpdateIncidentStatus', () => ({
  useUpdateIncidentStatus: () => ({
    updateStatus: mockUpdateStatus,
    isUpdating: false,
    error: null,
  }),
}));

jest.mock('../ResolutionModal', () => ({
  ResolutionModal: ({ incident }: { incident: Incident }) => (
    <div role="dialog">Resolution modal for {incident.id}</div>
  ),
}));

const incident: Incident = {
  id: 'INC001',
  title: 'Memory leak in auth service',
  description: 'Auth service memory grows unbounded',
  severity: 'high',
  status: 'open',
  created_at: '2026-01-17T10:30:00',
  affected_services: ['auth-service'],
};

describe('StatusDropdown resolved interception', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('opens the resolution modal instead of updating status when Resolved is selected', async () => {
    render(<StatusDropdown incident={incident} />);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: /incident status/i }), 'resolved');

    expect(screen.getByRole('dialog')).toHaveTextContent('Resolution modal for INC001');
    expect(mockUpdateStatus).not.toHaveBeenCalled();
  });

  it('updates status directly for non-resolved statuses', async () => {
    render(<StatusDropdown incident={incident} />);

    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: /incident status/i }),
      'investigating'
    );

    expect(mockUpdateStatus).toHaveBeenCalledWith('INC001', 'investigating');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
