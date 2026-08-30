import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Admin } from './Admin';

jest.mock('../services/api', () => ({
  api: {
    getLLMConfig: jest.fn().mockResolvedValue({}),
    getLoggingConfig: jest.fn().mockResolvedValue({}),
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

  it('renders all themes and persists the selected theme', () => {
    render(<Admin />);

    expect(screen.getAllByRole('radio')).toHaveLength(5);
    expect(screen.getByRole('radio', { name: 'Purple' })).toHaveAttribute('aria-checked', 'true');

    userEvent.click(screen.getByRole('radio', { name: 'Dark' }));

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'true');
  });
});
