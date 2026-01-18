import React from 'react';
import { render, screen } from '@testing-library/react';
import { Message } from './Message';

describe('Message', () => {
  it('renders user text message correctly', () => {
    render(<Message content="Hello world" isUser={true} />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('renders assistant text message correctly', () => {
    render(<Message content="Assistant response" isUser={false} />);
    expect(screen.getByText('Assistant response')).toBeInTheDocument();
  });

  it('renders agent response correctly', () => {
    const response = {
      incident_id: 'INC001',
      resolution_steps: ['Step 1', 'Step 2'],
      related_knowledge: ['Knowledge 1'],
      correlated_changes: ['Change 1'],
      summary: 'Test summary',
      confidence: 0.95,
    };

    render(<Message content={response} isUser={false} />);

    expect(screen.getByText('Resolution Analysis')).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
    expect(screen.getByText('Resolution Steps')).toBeInTheDocument();
    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
    expect(screen.getByText('Related Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Knowledge 1')).toBeInTheDocument();
    expect(screen.getByText('Correlated Changes')).toBeInTheDocument();
    expect(screen.getByText('Change 1')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 95%')).toBeInTheDocument();
  });
});
