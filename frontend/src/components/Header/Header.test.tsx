import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from './Header';

describe('Header', () => {
  const mockOnShowAdmin = jest.fn();

  beforeEach(() => {
    mockOnShowAdmin.mockClear();
  });

  it('renders gear and profile icons', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);
    
    expect(screen.getByTitle('Settings')).toBeInTheDocument();
    expect(screen.getByTitle('Profile')).toBeInTheDocument();
  });

  it('calls onShowAdmin when gear icon is clicked', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);
    
    const settingsButton = screen.getByTitle('Settings');
    fireEvent.click(settingsButton);
    
    expect(mockOnShowAdmin).toHaveBeenCalledTimes(1);
  });

  it('shows active state on gear icon when showingAdmin is true', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={true} />);
    
    const settingsButton = screen.getByTitle('Settings');
    expect(settingsButton).toHaveClass('active');
  });

  it('opens dropdown when profile icon is clicked', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);
    
    const profileButton = screen.getByTitle('Profile');
    fireEvent.click(profileButton);
    
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('closes dropdown when clicking outside', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);
    
    const profileButton = screen.getByTitle('Profile');
    fireEvent.click(profileButton);
    
    expect(screen.getByText('Settings')).toBeInTheDocument();
    
    // Click outside the dropdown
    fireEvent.mouseDown(document.body);
    
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });
});
