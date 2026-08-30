import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Admin } from './Admin';

jest.mock('../services/api', () => ({
  api: {
    getLLMConfig: jest.fn().mockResolvedValue({
      provider: 'ollama',
      model: 'test-model',
      temperature: 0,
      connection_details: {},
    }),
    getLoggingConfig: jest.fn().mockResolvedValue({ level: 'INFO', enable_tracing: false }),
    getAgentPrompts: jest.fn().mockResolvedValue({ prompts: {} }),
    getAccuracyMetrics: jest.fn().mockResolvedValue({}),
    getPromptLogs: jest.fn().mockResolvedValue({ logs: [] }),
  },
}));

describe('Admin theme picker', () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
  });

  it('renders five themes and persists the selected theme', async () => {
    render(<Admin />);

    await waitFor(() => expect(screen.queryByText('Loading configuration...')).not.toBeInTheDocument());
    expect(screen.getAllByRole('radio')).toHaveLength(5);

    fireEvent.click(screen.getByRole('radio', { name: 'Dark' }));

    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'true');
  });
});
