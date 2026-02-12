import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentResultsTabs } from './AgentResultsTabs';
import { AgentResults } from '../../types/incident';

// Mock alert
global.alert = jest.fn();

describe('AgentResultsTabs - Run Script Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  const mockRemediationResults: AgentResults = {
    remediation_results: {
      source: 'remediation_agent',
      incident_id: 'INC001',
      total_count: 2,
      remediations: [
        {
          id: 'REM001',
          title: 'Restart Database Service',
          description: 'Restart the database service to resolve connection issues',
          risk_level: 'low',
          confidence_score: 0.9,
          estimated_duration: '5 minutes',
          prerequisites: ['Verify no active transactions', 'Backup current state'],
          script: 'systemctl restart postgresql'
        },
        {
          id: 'REM002',
          title: 'Clear Cache',
          description: 'Clear application cache',
          risk_level: 'medium',
          confidence_score: 0.7,
          estimated_duration: '2 minutes',
          prerequisites: [],
          script: 'redis-cli FLUSHALL'
        }
      ]
    }
  };

  it('renders Run Script button with correct text', () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Check if Run Script buttons are present
    const runButtons = screen.getAllByRole('button', { name: /Run Script/i });
    expect(runButtons).toHaveLength(2);
  });

  it('shows loading state when running script', async () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Click first Run Script button
    const runButtons = screen.getAllByRole('button', { name: /Run Script/i });
    fireEvent.click(runButtons[0]);
    
    // Check for loading state
    await waitFor(() => {
      expect(screen.getByText('⏳ Running...')).toBeInTheDocument();
    });
    
    // Button should be disabled during execution
    const runningButton = screen.getByText('⏳ Running...');
    expect(runningButton).toBeDisabled();
  });

  it('simulates script execution and shows success', async () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Click first Run Script button
    const runButtons = screen.getAllByRole('button', { name: /Run Script/i });
    fireEvent.click(runButtons[0]);
    
    // Fast-forward time to complete simulation
    jest.advanceTimersByTime(2500);
    
    // Wait for success alert
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('✅ Script Executed Successfully!')
      );
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('REM001')
      );
    });
  });

  it('allows running different scripts sequentially', async () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Click first Run Script button
    const runButtons = screen.getAllByRole('button', { name: /Run Script/i });
    fireEvent.click(runButtons[0]);
    
    // Fast-forward time to complete first execution
    jest.advanceTimersByTime(2500);
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledTimes(1);
    });
    
    // Now click second Run Script button
    const newRunButtons = screen.getAllByRole('button', { name: /Run Script/i });
    fireEvent.click(newRunButtons[1]);
    
    // Fast-forward time to complete second execution
    jest.advanceTimersByTime(2500);
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledTimes(2);
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('REM002')
      );
    });
  });

  it('displays remediation details correctly', () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Check for remediation titles
    expect(screen.getByText('Restart Database Service')).toBeInTheDocument();
    expect(screen.getByText('Clear Cache')).toBeInTheDocument();
    
    // Check for risk levels
    expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();
    
    // Check for confidence scores
    expect(screen.getByText('Confidence: 90%')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 70%')).toBeInTheDocument();
    
    // Check for scripts
    expect(screen.getByText('systemctl restart postgresql')).toBeInTheDocument();
    expect(screen.getByText('redis-cli FLUSHALL')).toBeInTheDocument();
  });

  it('displays prerequisites when available', () => {
    render(<AgentResultsTabs agentResults={mockRemediationResults} />);
    
    // Click on Remediations tab
    fireEvent.click(screen.getByText('Remediations'));
    
    // Check for prerequisites
    expect(screen.getByText('Prerequisites:')).toBeInTheDocument();
    expect(screen.getByText('Verify no active transactions')).toBeInTheDocument();
    expect(screen.getByText('Backup current state')).toBeInTheDocument();
  });
});
