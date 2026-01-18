import React from 'react';
import { AgentResponse } from '../../types/incident';
import styles from './Message.module.css';

interface MessageProps {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

export const Message: React.FC<MessageProps> = ({ content, isUser, isStreaming = false }) => {
  const renderContent = () => {
    if (typeof content === 'string') {
      return (
        <>
          <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>
          {isStreaming && <span className={styles.streamingIndicator}>●</span>}
        </>
      );
    }

    const response = content as AgentResponse;
    return (
      <>
        <h4 className={styles.sectionTitle}>Resolution Analysis</h4>
        <p>{response.summary}</p>

        {response.resolution_steps.length > 0 && (
          <>
            <h4 className={styles.sectionTitle}>Resolution Steps</h4>
            <ul className={styles.list}>
              {response.resolution_steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
          </>
        )}

        {response.correlated_changes.length > 0 && (
          <>
            <h4 className={styles.sectionTitle}>Correlated Changes</h4>
            <ul className={styles.list}>
              {response.correlated_changes.map((change, index) => (
                <li key={index}>{change}</li>
              ))}
            </ul>
          </>
        )}

        {response.related_knowledge.length > 0 && (
          <>
            <h4 className={styles.sectionTitle}>Related Knowledge</h4>
            <ul className={styles.list}>
              {response.related_knowledge.map((knowledge, index) => (
                <li key={index}>{knowledge}</li>
              ))}
            </ul>
          </>
        )}

        <p className={styles.confidence}>
          Confidence: {(response.confidence * 100).toFixed(0)}%
        </p>
      </>
    );
  };

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}>
      {renderContent()}
    </div>
  );
};
