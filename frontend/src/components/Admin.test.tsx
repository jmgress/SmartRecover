import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Admin } from './Admin';

jest.mock('../services/api', () => ({
  api: {
    getLLMConfig: jest.fn().mockResolvedValue({
      provider: 'ollama',
      model: 'test',
      temperature: 0,
      connection_details: {},
    }),
    getLoggingConfig: jest.fn().mockResolvedValue({
      level: 'INFO',
      enable_tracing: false,
    }),
    getAutomationConfig: jest.fn().mockResolvedValue({
      global_enabled: true,
      rules: [],
      recent_audit: [],
    }),
    getAgentPrompts: jest.fn().mockResolvedValue({ prompts: {} }),
    getAccuracyMetrics: jest.fn().mockResolvedValue({}),
    getPromptLogs: jest.fn().mockResolvedValue({}),
  },
}));

describe('Admin', () => {
  it('renders system configuration without a theme picker', async () => {
    render(<Admin />);

    await waitFor(() =>
      expect(screen.queryByText('Loading configuration...')).not.toBeInTheDocument()
    );

    expect(screen.getByText('Admin - System Configuration')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Automation' })).toBeInTheDocument();
    expect(screen.queryByRole('radiogroup')).not.toBeInTheDocument();
  });
});
