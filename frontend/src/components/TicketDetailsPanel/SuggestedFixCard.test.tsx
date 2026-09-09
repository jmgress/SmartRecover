import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SuggestedFixCard } from './SuggestedFixCard';
import { AutomationDecision, SuggestedFix } from '../../types/incident';

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
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument()
    );
    expect(writeText).toHaveBeenCalledWith(suggestedFix.script);
  });

  it('shows the simulated auto-remediation badge when automated', () => {
    const automationDecision: AutomationDecision = {
      automated: true,
      reason: 'auto-remediation simulated and audited',
      category: 'Database',
      threshold: 0.85,
      incident_confidence: 0.92,
      suggested_fix_confidence: 0.85,
      risk_level: 'low',
      severity: 'medium',
      suggested_fix_id: suggestedFix.id,
      audit_record_id: 'audit-1',
    };

    render(<SuggestedFixCard suggestedFix={suggestedFix} automationDecision={automationDecision} />);

    expect(screen.getByText('Auto-remediated (simulated)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '✓ Auto-remediated' })).toBeDisabled();
  });

  it('disables the run button and exposes the block reason when automation is blocked', () => {
    render(
      <SuggestedFixCard
        suggestedFix={suggestedFix}
        automationDecision={{
          automated: false,
          reason: 'global automation kill switch is off',
        }}
      />
    );

    const blockedButton = screen.getByRole('button', { name: 'Automation Blocked' });
    expect(blockedButton).toBeDisabled();
    expect(blockedButton.parentElement).toHaveAttribute('title', 'global automation kill switch is off');
  });
});
