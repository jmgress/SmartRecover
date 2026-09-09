import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatWidget } from './ChatWidget';

jest.mock('../ChatContainer', () => ({
  ChatContainer: () => <div>Chat messages</div>,
}));

jest.mock('../ChatInput', () => ({
  ChatInput: () => <div>Chat input</div>,
}));

describe('ChatWidget', () => {
  const defaultProps = {
    messages: [],
    selectedIncidentId: 'INC001',
    onSubmitQuery: jest.fn(),
    isStreaming: false,
    isOpen: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when no incident is selected', () => {
    const { container } = render(
      <ChatWidget {...defaultProps} selectedIncidentId={null} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the chat button when an incident is selected', () => {
    render(<ChatWidget {...defaultProps} />);
    expect(screen.getByRole('button', { name: 'Open chat' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onToggle when the chat button is clicked', async () => {
    render(<ChatWidget {...defaultProps} />);
    await userEvent.click(screen.getByRole('button', { name: 'Open chat' }));
    expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
  });

  it('shows the chat window with incident context when open', () => {
    render(<ChatWidget {...defaultProps} isOpen={true} />);
    expect(screen.getByRole('dialog', { name: 'Incident chat' })).toBeInTheDocument();
    expect(screen.getByText('Chat — INC0000001')).toBeInTheDocument();
    expect(screen.getByText('Chat messages')).toBeInTheDocument();
    expect(screen.getByText('Chat input')).toBeInTheDocument();
  });

  it('calls onToggle when the close button is clicked', async () => {
    render(<ChatWidget {...defaultProps} isOpen={true} />);
    await userEvent.click(screen.getByRole('button', { name: 'Close chat' }));
    expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
  });
});
