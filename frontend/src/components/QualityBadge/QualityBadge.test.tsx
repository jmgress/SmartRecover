import React from 'react';
import { render, screen } from '@testing-library/react';
import { QualityBadge } from './QualityBadge';

describe('QualityBadge', () => {
  it('renders quality badge with score', () => {
    render(<QualityBadge level="good" score={0.85} showScore={true} />);
    expect(screen.getByText('Quality: 85%')).toBeInTheDocument();
  });

  it('renders quality badge with "Good Quality" when score not shown', () => {
    render(<QualityBadge level="good" />);
    expect(screen.getByText('Quality: Good Quality')).toBeInTheDocument();
  });

  it('renders quality badge with "Needs Improvement" when score not shown', () => {
    render(<QualityBadge level="warning" />);
    expect(screen.getByText('Quality: Needs Improvement')).toBeInTheDocument();
  });

  it('renders quality badge with "Poor Quality" when score not shown', () => {
    render(<QualityBadge level="poor" />);
    expect(screen.getByText('Quality: Poor Quality')).toBeInTheDocument();
  });

  it('displays score when showScore is true', () => {
    render(<QualityBadge level="good" score={0.85} showScore={true} />);
    expect(screen.getByText('Quality: 85%')).toBeInTheDocument();
  });

  it('does not display score percentage when showScore is false', () => {
    render(<QualityBadge level="good" score={0.85} showScore={false} />);
    expect(screen.getByText('Quality: Good Quality')).toBeInTheDocument();
    expect(screen.queryByText('Quality: 85%')).not.toBeInTheDocument();
  });

  it('does not display score percentage when showScore is undefined', () => {
    render(<QualityBadge level="good" score={0.85} />);
    expect(screen.getByText('Quality: Good Quality')).toBeInTheDocument();
    expect(screen.queryByText('Quality: 85%')).not.toBeInTheDocument();
  });

  it('applies correct CSS class', () => {
    const { container } = render(<QualityBadge level="good" />);
    const badge = container.querySelector('.quality');
    expect(badge).toBeInTheDocument();
  });

  it('rounds score correctly', () => {
    render(<QualityBadge level="good" score={0.854} showScore={true} />);
    expect(screen.getByText('Quality: 85%')).toBeInTheDocument();
  });

  it('rounds score correctly for warning level', () => {
    render(<QualityBadge level="warning" score={0.654} showScore={true} />);
    expect(screen.getByText('Quality: 65%')).toBeInTheDocument();
  });

  it('rounds score correctly for poor level', () => {
    render(<QualityBadge level="poor" score={0.234} showScore={true} />);
    expect(screen.getByText('Quality: 23%')).toBeInTheDocument();
  });
});
