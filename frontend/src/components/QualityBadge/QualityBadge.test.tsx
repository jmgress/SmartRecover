import React from 'react';
import { render, screen } from '@testing-library/react';
import { QualityBadge } from './QualityBadge';

describe('QualityBadge', () => {
  it('renders good quality badge', () => {
    render(<QualityBadge level="good" />);
    expect(screen.getByText('Good Quality')).toBeInTheDocument();
  });

  it('renders warning quality badge', () => {
    render(<QualityBadge level="warning" />);
    expect(screen.getByText('Needs Improvement')).toBeInTheDocument();
  });

  it('renders poor quality badge', () => {
    render(<QualityBadge level="poor" />);
    expect(screen.getByText('Poor Quality')).toBeInTheDocument();
  });

  it('displays score when showScore is true', () => {
    render(<QualityBadge level="good" score={0.85} showScore={true} />);
    expect(screen.getByText(/Good Quality \(85%\)/)).toBeInTheDocument();
  });

  it('does not display score when showScore is false', () => {
    render(<QualityBadge level="good" score={0.85} showScore={false} />);
    expect(screen.getByText('Good Quality')).toBeInTheDocument();
    expect(screen.queryByText(/85%/)).not.toBeInTheDocument();
  });

  it('does not display score when showScore is undefined', () => {
    render(<QualityBadge level="good" score={0.85} />);
    expect(screen.getByText('Good Quality')).toBeInTheDocument();
    expect(screen.queryByText(/85%/)).not.toBeInTheDocument();
  });

  it('applies correct CSS class for good level', () => {
    const { container } = render(<QualityBadge level="good" />);
    const badge = container.querySelector('.good');
    expect(badge).toBeInTheDocument();
  });

  it('applies correct CSS class for warning level', () => {
    const { container } = render(<QualityBadge level="warning" />);
    const badge = container.querySelector('.warning');
    expect(badge).toBeInTheDocument();
  });

  it('applies correct CSS class for poor level', () => {
    const { container } = render(<QualityBadge level="poor" />);
    const badge = container.querySelector('.poor');
    expect(badge).toBeInTheDocument();
  });

  it('rounds score correctly', () => {
    render(<QualityBadge level="good" score={0.854} showScore={true} />);
    expect(screen.getByText(/Good Quality \(85%\)/)).toBeInTheDocument();
  });
});
