import React from 'react';
import { ChatContainer } from '../ChatContainer';
import { ChatInput } from '../ChatInput';
import { AgentResponse } from '../../types/incident';
import { formatIncidentNumber } from '../../utils/formatIncidentNumber';
import styles from './ChatWidget.module.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

interface ChatWidgetProps {
  messages: ChatMessage[];
  selectedIncidentId: string | null;
  onSubmitQuery: (query: string) => void;
  isStreaming: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({
  messages,
  selectedIncidentId,
  onSubmitQuery,
  isStreaming,
  isOpen,
  onToggle,
}) => {
  if (!selectedIncidentId) {
    return null;
  }

  return (
    <>
      {isOpen && (
        <div className={styles.chatWindow} role="dialog" aria-label="Incident chat">
          <div className={styles.chatHeader}>
            <span className={styles.chatTitle}>
              Chat — {formatIncidentNumber(selectedIncidentId)}
            </span>
            <button
              type="button"
              className={styles.closeButton}
              onClick={onToggle}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>
          <div className={styles.chatBody}>
            <ChatContainer messages={messages} selectedIncidentId={selectedIncidentId} />
            <ChatInput
              onSubmit={onSubmitQuery}
              disabled={!selectedIncidentId}
              loading={isStreaming}
            />
          </div>
        </div>
      )}
      <button
        type="button"
        className={styles.chatButton}
        onClick={onToggle}
        aria-label={isOpen ? 'Minimize chat' : 'Open chat'}
      >
        {isOpen ? '✕' : '💬'}
      </button>
    </>
  );
};
