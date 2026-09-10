import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResolutionModal } from './ResolutionModal';
import { api } from '../../services/api';
import { Incident } from '../../types/incident';

jest.mock('../../services/api', () => ({
  api: {
    draftResolution: jest.fn(),
    submitResolution: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;

const incident: Incident = {
  id: 'INC001',
  title: 'Memory leak in auth service',
  description: 'Auth service memory grows unbounded',
  severity: 'high',
  status: 'investigating',
  created_at: '2026-01-17T10:30:00',
  affected_services: ['auth-service'],
};

describe('ResolutionModal', () => {
  const onClose = jest.fn();
  const onResolved = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the resolution form', () => {
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText('Resolution text')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate ai draft/i })).toBeInTheDocument();
  });

  it('populates the textarea with the AI draft', async () => {
    mockedApi.draftResolution.mockResolvedValue({
      incident_id: 'INC001',
      draft: 'Root cause was a leak; restarted service and verified.',
      source: 'resolution_agent',
    });
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);

    await userEvent.click(screen.getByRole('button', { name: /generate ai draft/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Resolution text')).toHaveValue(
        'Root cause was a leak; restarted service and verified.'
      );
    });
    expect(mockedApi.draftResolution).toHaveBeenCalledWith('INC001');
  });

  it('shows grade feedback and stays open when the resolution fails grading', async () => {
    mockedApi.submitResolution.mockResolvedValue({
      incident_id: 'INC001',
      grade: {
        score: 0.05,
        passed: false,
        threshold: 0.7,
        feedback: 'Describe the root cause and fix.',
        issues: ['"resolved" is a generic phrase, not a resolution.'],
      },
      record: null,
    });
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);

    await userEvent.type(screen.getByLabelText('Resolution text'), 'resolved');
    await userEvent.click(screen.getByRole('button', { name: /submit resolution/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Resolution rejected');
    expect(screen.getByText('Describe the root cause and fix.')).toBeInTheDocument();
    expect(onResolved).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('notifies the parent and closes when the resolution passes', async () => {
    mockedApi.submitResolution.mockResolvedValue({
      incident_id: 'INC001',
      grade: { score: 0.9, passed: true, threshold: 0.7, feedback: 'Good.', issues: [] },
      record: {
        id: 'r1',
        incident_id: 'INC001',
        resolution_text: 'Detailed resolution.',
        grade: { score: 0.9, passed: true, threshold: 0.7, feedback: 'Good.', issues: [] },
        created_at: '2026-01-17T12:00:00Z',
      },
    });
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);

    await userEvent.type(
      screen.getByLabelText('Resolution text'),
      'Root cause was a memory leak; patched and verified recovery.'
    );
    await userEvent.click(screen.getByRole('button', { name: /submit resolution/i }));

    await waitFor(() => {
      expect(onResolved).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'INC001', status: 'resolved' })
      );
    });
    expect(onClose).toHaveBeenCalled();
  });

  it('disables submit while the textarea is empty', () => {
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);
    expect(screen.getByRole('button', { name: /submit resolution/i })).toBeDisabled();
  });

  it('shows an error when submission fails', async () => {
    mockedApi.submitResolution.mockRejectedValue(new Error('Server unavailable'));
    render(<ResolutionModal incident={incident} onClose={onClose} onResolved={onResolved} />);

    await userEvent.type(screen.getByLabelText('Resolution text'), 'Some resolution text');
    await userEvent.click(screen.getByRole('button', { name: /submit resolution/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Server unavailable');
  });
});
