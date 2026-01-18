import React, { useState } from 'react';
import { LoadingSpinner } from '../LoadingSpinner';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  onSubmit: (query: string) => void;
  disabled: boolean;
  loading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSubmit, disabled, loading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query);
      setQuery('');
    }
  };

  return (
    <div className={styles.inputArea}>
      <form className={styles.inputForm} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder="Ask about this incident..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled || loading}
        />
        <button
          type="submit"
          className={styles.button}
          disabled={disabled || loading || !query.trim()}
        >
          {loading ? <LoadingSpinner /> : 'Resolve'}
        </button>
      </form>
    </div>
  );
};
