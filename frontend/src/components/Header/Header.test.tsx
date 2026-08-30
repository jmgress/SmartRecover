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

  it('closes dropdown when clicking profile button again', () => {
    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);
    
    const profileButton = screen.getByTitle('Profile');
    
    // Open dropdown
    fireEvent.click(profileButton);
    expect(screen.getByText('Settings')).toBeInTheDocument();
    
    // Close dropdown by clicking profile button again
    fireEvent.click(profileButton);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('renders all themes in the profile dropdown and persists the selected theme', () => {
    localStorage.clear();
    document.documentElement.dataset.theme = 'purple';

    render(<Header onShowAdmin={mockOnShowAdmin} showingAdmin={false} />);

    fireEvent.click(screen.getByTitle('Profile'));

    expect(screen.getAllByRole('radio')).toHaveLength(5);
    expect(screen.getByRole('radio', { name: 'Purple' })).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(screen.getByRole('radio', { name: 'Dark' }));

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'true');
  });
});
