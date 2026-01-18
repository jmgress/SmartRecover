import React from 'react';
import { render, screen } from '@testing-library/react';
import { SeverityBadge } from './SeverityBadge';

describe('SeverityBadge', () => {
  it('renders high severity correctly', () => {
    render(<SeverityBadge severity="high" />);
    const badge = screen.getByText('high');
    expect(badge).toBeInTheDocument();
  });

  it('renders medium severity correctly', () => {
    render(<SeverityBadge severity="medium" />);
    const badge = screen.getByText('medium');
    expect(badge).toBeInTheDocument();
  });

  it('renders low severity correctly', () => {
    render(<SeverityBadge severity="low" />);
    const badge = screen.getByText('low');
    expect(badge).toBeInTheDocument();
  });
});
