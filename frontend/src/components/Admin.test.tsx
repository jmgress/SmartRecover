import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Admin } from './Admin';
import { api } from '../services/api';

jest.mock('../services/api', () => ({
  api: {
    testLLM: jest.fn(),
    getLLMConfig: jest.fn(),
    getLoggingConfig: jest.fn(),
    updateLoggingConfig: jest.fn(),
    getAutomationRules: jest.fn(),
    updateAutomationRules: jest.fn(),
    getAutomationAudit: jest.fn(),
    clearAutomationAudit: jest.fn(),
    getAgentPrompts: jest.fn(),
    updateAgentPrompt: jest.fn(),
    resetAgentPrompts: jest.fn(),
    getAccuracyMetrics: jest.fn(),
    getPromptLogs: jest.fn(),
    clearPromptLogs: jest.fn(),
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
    (api.testLLM as jest.Mock).mockResolvedValue({ status: 'ok', llm_response: 'working' });
    (api.getLoggingConfig as jest.Mock).mockResolvedValue({
      level: 'INFO',
      enable_tracing: false,
    });
    (api.updateLoggingConfig as jest.Mock).mockResolvedValue({
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
          Application: {
            enabled: false,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.85,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
        },
      },
      categories: ['Database', 'Application'],
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
          Application: {
            enabled: true,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.85,
            max_risk_level: 'low',
            max_severity: 'critical',
          },
        },
      },
      categories: ['Database', 'Application'],
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
    (api.getAgentPrompts as jest.Mock).mockResolvedValue({
      prompts: {
        orchestrator: {
          current: 'Prompt text',
          default: 'Prompt text',
          is_custom: false,
        },
      },
    });
    (api.updateAgentPrompt as jest.Mock).mockResolvedValue({
      current: 'Prompt text',
      default: 'Prompt text',
      is_custom: false,
    });
    (api.resetAgentPrompts as jest.Mock).mockResolvedValue({ message: 'reset' });
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
    (api.clearPromptLogs as jest.Mock).mockResolvedValue({ message: 'cleared' });
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
          Application: {
            enabled: false,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.85,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
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

  it('renders the automation section and toggles the global kill switch warning', async () => {
    render(<Admin />);

    await userEvent.click(screen.getByRole('button', { name: 'Automation' }));

    expect(await screen.findByRole('heading', { name: 'Automation' })).toBeInTheDocument();
    const globalKillSwitch = screen.getByLabelText('Enable global automation kill switch override');
    expect(globalKillSwitch).toBeChecked();
    expect(screen.queryByText(/Global kill switch is off/i)).not.toBeInTheDocument();

    await userEvent.click(globalKillSwitch);

    expect(screen.getByText(/Global kill switch is off/i)).toBeInTheDocument();
  });

  it('toggles category automation and saves the updated rule set', async () => {
    render(<Admin />);

    await userEvent.click(screen.getByRole('button', { name: 'Automation' }));

    const applicationToggle = await screen.findByRole('checkbox', {
      name: 'Application automation enabled',
    });
    expect(applicationToggle).not.toBeChecked();

    await userEvent.click(applicationToggle);
    expect(applicationToggle).toBeChecked();

    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Application max severity' }),
      'critical'
    );
    await userEvent.click(screen.getByRole('button', { name: 'Update Automation Rules' }));

    await waitFor(() =>
      expect(api.updateAutomationRules).toHaveBeenCalledWith({
        global_enabled: true,
        rules: {
          Database: {
            enabled: true,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.8,
            max_risk_level: 'low',
            max_severity: 'medium',
          },
          Application: {
            enabled: true,
            confidence_threshold: 0.85,
            min_fix_confidence: 0.85,
            max_risk_level: 'low',
            max_severity: 'critical',
          },
        },
      })
    );
  });
});
