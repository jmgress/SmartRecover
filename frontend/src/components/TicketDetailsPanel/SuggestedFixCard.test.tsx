import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SuggestedFixCard } from './SuggestedFixCard';
import { SuggestedFix } from '../../types/incident';

const suggestedFix: SuggestedFix = {
  id: 'rem-db-001',
  title: 'Restart Database Connection Pool',
  description: 'Restarts the database connection pool to clear stale connections.',
  script: 'kubectl rollout restart deployment/db-connection-pool',
  risk_level: 'low',
  estimated_duration: '2-3 minutes',
  prerequisites: ['Database backup completed'],
  confidence_score: 0.85,
  rationale: 'Highest-confidence remediation (85%) of 2 candidate(s)',
  source: 'remediation_engine',
};

describe('SuggestedFixCard', () => {
  it('renders the suggested fix details', () => {
    render(<SuggestedFixCard suggestedFix={suggestedFix} />);

    expect(screen.getByText(/suggested fix/i)).toBeInTheDocument();
    expect(screen.getByText('Restart Database Connection Pool')).toBeInTheDocument();
    expect(screen.getByText(/low risk/i)).toBeInTheDocument();
    expect(screen.getByText(/confidence: 85%/i)).toBeInTheDocument();
    expect(
      screen.getByText('kubectl rollout restart deployment/db-connection-pool')
    ).toBeInTheDocument();
    expect(screen.getByText(/highest-confidence remediation/i)).toBeInTheDocument();
    expect(screen.getByText('Database backup completed')).toBeInTheDocument();
  });

  it('exposes run and copy actions', async () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(<SuggestedFixCard suggestedFix={suggestedFix} />);

    expect(screen.getByRole('button', { name: /run script/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /copy script/i }));
    expect(writeText).toHaveBeenCalledWith(suggestedFix.script);
  });
});
