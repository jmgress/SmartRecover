import React, { useEffect, useRef } from 'react';
import { AgentResponse } from '../../types/incident';
import { Message } from '../Message';
import styles from './ChatContainer.module.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

interface ChatContainerProps {
  messages: ChatMessage[];
  selectedIncidentId: string | null;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ messages, selectedIncidentId }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          {selectedIncidentId ? `Incident: ${selectedIncidentId}` : 'Select an incident to begin'}
        </h1>
      </div>
      <div className={styles.chatContainer} ref={containerRef}>
        {messages.length === 0 ? (
          <Message
            content="Welcome to the Incident Resolver. Select an incident from the sidebar and ask questions to get resolution guidance."
            isUser={false}
          />
        ) : (
          messages.map((msg, index) => (
            <Message 
              key={index} 
              content={msg.content} 
              isUser={msg.isUser}
              isStreaming={msg.isStreaming}
            />
          ))
        )}
      </div>
    </div>
  );
};
