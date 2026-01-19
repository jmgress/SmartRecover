import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterButtons, IncidentStatusFilter } from './FilterButtons';

describe('FilterButtons', () => {
  it('renders all filter buttons', () => {
    const mockOnFilterChange = jest.fn();
    render(<FilterButtons activeFilter="open" onFilterChange={mockOnFilterChange} />);

    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('Investigating')).toBeInTheDocument();
    expect(screen.getByText('Closed')).toBeInTheDocument();
  });

  it('highlights the active filter button', () => {
    const mockOnFilterChange = jest.fn();
    const { rerender } = render(<FilterButtons activeFilter="open" onFilterChange={mockOnFilterChange} />);

    let openButton = screen.getByText('Open');
    expect(openButton).toHaveClass('active');

    rerender(<FilterButtons activeFilter="investigating" onFilterChange={mockOnFilterChange} />);
    
    let investigatingButton = screen.getByText('Investigating');
    expect(investigatingButton).toHaveClass('active');
  });

  it('calls onFilterChange when a filter button is clicked', () => {
    const mockOnFilterChange = jest.fn();
    render(<FilterButtons activeFilter="open" onFilterChange={mockOnFilterChange} />);

    const investigatingButton = screen.getByText('Investigating');
    fireEvent.click(investigatingButton);

    expect(mockOnFilterChange).toHaveBeenCalledWith('investigating');
  });

  it('calls onFilterChange with correct filter value for each button', () => {
    const mockOnFilterChange = jest.fn();
    render(<FilterButtons activeFilter="open" onFilterChange={mockOnFilterChange} />);

    fireEvent.click(screen.getByText('Open'));
    expect(mockOnFilterChange).toHaveBeenCalledWith('open');

    fireEvent.click(screen.getByText('Investigating'));
    expect(mockOnFilterChange).toHaveBeenCalledWith('investigating');

    fireEvent.click(screen.getByText('Closed'));
    expect(mockOnFilterChange).toHaveBeenCalledWith('closed');
  });
});
