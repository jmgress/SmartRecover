import React from 'react';
import { ChatContainer } from '../ChatContainer';
import { ChatInput } from '../ChatInput';
import { AgentResponse } from '../../types/incident';
import styles from './ChatPanel.module.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  selectedIncidentId: string | null;
  onSubmitQuery: (query: string) => void;
  isStreaming: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  selectedIncidentId,
  onSubmitQuery,
  isStreaming,
}) => {
  return (
    <div className={styles.chatPanel}>
      <ChatContainer messages={messages} selectedIncidentId={selectedIncidentId} />
      <ChatInput
        onSubmit={onSubmitQuery}
        disabled={!selectedIncidentId}
        loading={isStreaming}
      />
    </div>
  );
};
