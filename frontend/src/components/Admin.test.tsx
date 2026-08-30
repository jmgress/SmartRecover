import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    getAgentPrompts: jest.fn().mockResolvedValue({ prompts: {} }),
    getAccuracyMetrics: jest.fn().mockResolvedValue({}),
    getPromptLogs: jest.fn().mockResolvedValue({}),
  },
}));

describe('Admin theme picker', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.dataset.theme = 'purple';
  });

  it('renders all themes and persists the selected theme', async () => {
    render(<Admin />);

    await waitFor(() =>
      expect(screen.queryByText('Loading configuration...')).not.toBeInTheDocument()
    );

    expect(screen.getAllByRole('radio')).toHaveLength(5);
    expect(screen.getByRole('radio', { name: 'Purple' })).toHaveAttribute('aria-checked', 'true');

    await userEvent.click(screen.getByRole('radio', { name: 'Dark' }));

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'true');
  });
});
