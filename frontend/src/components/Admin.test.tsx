import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Admin } from './Admin';
import { api } from '../services/api';

jest.mock('../services/api', () => ({
  api: {
    getLLMConfig: jest.fn(),
    getLoggingConfig: jest.fn(),
    getAutomationRules: jest.fn(),
    updateAutomationRules: jest.fn(),
    getAutomationAudit: jest.fn(),
    clearAutomationAudit: jest.fn(),
    getAgentPrompts: jest.fn(),
    getAccuracyMetrics: jest.fn(),
    getPromptLogs: jest.fn(),
  },
}));

describe('Admin', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.confirm = jest.fn().mockReturnValue(true);
    (api.getLLMConfig as jest.Mock).mockResolvedValue({
      provider: 'ollama',
      model: 'test',
      temperature: 0,
      connection_details: {},
    });
    (api.getLoggingConfig as jest.Mock).mockResolvedValue({
      level: 'INFO',
      enable_tracing: false,
    });
    (api.getAutomationRules as jest.Mock).mockResolvedValue({
      rules: {
        global_enabled: true,
        rules: {
          Database: {
            enabled: true,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.8,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
        },
      },
      categories: ['Database'],
      defaults: {
        enabled: false,
        confidence_threshold: 0.85,
        min_fix_confidence: 0.85,
        max_risk_level: 'low',
        max_severity: 'medium',
      },
    });
    (api.updateAutomationRules as jest.Mock).mockResolvedValue({
      rules: {
        global_enabled: true,
        rules: {
          Database: {
            enabled: true,
            confidence_threshold: 0.6,
            min_fix_confidence: 0.8,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
        },
      },
      categories: ['Database'],
      defaults: {
        enabled: false,
        confidence_threshold: 0.85,
        min_fix_confidence: 0.85,
        max_risk_level: 'low',
        max_severity: 'medium',
      },
    });
    (api.getAutomationAudit as jest.Mock).mockResolvedValue([
      {
        id: 'audit-1',
        incident_id: 'INC001',
        automated: false,
        reason: 'global automation kill switch is off',
        category: 'Database',
        created_at: '2026-09-09T16:00:00Z',
      },
    ]);
    (api.clearAutomationAudit as jest.Mock).mockResolvedValue({ message: 'cleared' });
    (api.getAgentPrompts as jest.Mock).mockResolvedValue({ prompts: {} });
    (api.getAccuracyMetrics as jest.Mock).mockResolvedValue({
      categories: [],
      overall_accuracy: 0,
      total_exclusions: 0,
      total_items_returned: 0,
    });
    (api.getPromptLogs as jest.Mock).mockResolvedValue({
      logs: [],
      total_count: 0,
    });
  });

  it('renders system configuration without a theme picker', async () => {
    render(<Admin />);

    await waitFor(() =>
      expect(screen.queryByText('Loading configuration...')).not.toBeInTheDocument()
    );

    expect(screen.getByText('Admin - System Configuration')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Automation' })).toBeInTheDocument();
    expect(screen.queryByRole('radiogroup')).not.toBeInTheDocument();
  });

  it('updates automation rules and clears the audit log from the automation tab', async () => {
    render(<Admin />);

    await userEvent.click(screen.getByRole('button', { name: 'Automation' }));

    expect(await screen.findByText('Recent Automation Audit')).toBeInTheDocument();

    await userEvent.clear(screen.getByRole('spinbutton', { name: 'Database confidence threshold' }));
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Database confidence threshold' }), '0.6');
    await userEvent.click(screen.getByRole('button', { name: 'Update Automation Rules' }));

    await waitFor(() =>
      expect(api.updateAutomationRules).toHaveBeenCalledWith({
        global_enabled: true,
        rules: {
          Database: {
            enabled: true,
            confidence_threshold: 0.6,
            min_fix_confidence: 0.8,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
        },
      })
    );

    await userEvent.click(screen.getByRole('button', { name: 'Clear Audit' }));

    await waitFor(() => expect(api.clearAutomationAudit).toHaveBeenCalled());
    expect(api.getAutomationAudit).toHaveBeenCalledTimes(2);
  });
});
