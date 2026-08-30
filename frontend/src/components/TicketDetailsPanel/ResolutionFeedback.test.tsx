import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api } from '../../services/api';
import { ResolutionFeedback } from './ResolutionFeedback';

jest.mock('../../services/api', () => ({
  api: {
    submitFeedback: jest.fn(),
  },
}));

describe('ResolutionFeedback', () => {
  it('submits a rating and optional comment', async () => {
    const submitFeedback = api.submitFeedback as jest.Mock;
    submitFeedback.mockResolvedValue({});
    render(<ResolutionFeedback incidentId="INC001" />);

    await userEvent.type(screen.getByLabelText(/optional feedback comment/i), 'This solved the problem');
    await userEvent.click(screen.getByRole('button', { name: /^helpful$/i }));

    expect(submitFeedback).toHaveBeenCalledWith({
      incident_id: 'INC001',
      rating: 'helpful',
      comment: 'This solved the problem',
    });
    expect(await screen.findByText(/thanks for your feedback/i)).toBeInTheDocument();
  });
});
