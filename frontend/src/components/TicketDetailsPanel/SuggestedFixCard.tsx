import React, { useState } from 'react';
import { SuggestedFix } from '../../types/incident';
import styles from './SuggestedFixCard.module.css';

interface SuggestedFixCardProps {
  suggestedFix: SuggestedFix;
}

export const SuggestedFixCard: React.FC<SuggestedFixCardProps> = ({ suggestedFix }) => {
  const [copied, setCopied] = useState(false);
  const [executing, setExecuting] = useState(false);

  const riskClass =
    suggestedFix.risk_level === 'high'
      ? styles.riskHigh
      : suggestedFix.risk_level === 'medium'
        ? styles.riskMedium
        : styles.riskLow;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(suggestedFix.script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable (e.g. insecure context); ignore
    }
  };

  const handleRun = async () => {
    setExecuting(true);
    try {
      // Simulated execution for demo purposes, matching remediation tab behavior
      await new Promise((resolve) => setTimeout(resolve, 1500));
      alert(
        `✅ Script Executed Successfully!\n\nSuggested Fix: ${suggestedFix.title}\n\nThe following script has been simulated:\n${suggestedFix.script}`
      );
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className={styles.card}>
      <div className={styles.headerRow}>
        <span className={styles.label}>⚡ Suggested Fix</span>
        <span className={`${styles.badge} ${riskClass}`}>
          {suggestedFix.risk_level.toUpperCase()} RISK
        </span>
        <span className={`${styles.badge} ${styles.confidence}`}>
          Confidence: {(suggestedFix.confidence_score * 100).toFixed(0)}%
        </span>
      </div>

      <h4 className={styles.title}>{suggestedFix.title}</h4>
      <p className={styles.description}>{suggestedFix.description}</p>

      <div className={styles.rationale}>
        <strong>Why this fix:</strong> {suggestedFix.rationale}
      </div>

      <pre className={styles.script}>
        <code>{suggestedFix.script}</code>
      </pre>

      <div className={styles.meta}>
        {suggestedFix.estimated_duration && (
          <span>
            <strong>Duration:</strong> {suggestedFix.estimated_duration}
          </span>
        )}
      </div>

      {suggestedFix.prerequisites && suggestedFix.prerequisites.length > 0 && (
        <div className={styles.prerequisites}>
          <strong>Prerequisites:</strong>
          <ul>
            {suggestedFix.prerequisites.map((prereq, idx) => (
              <li key={idx}>{prereq}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.actions}>
        <button className={styles.runButton} onClick={handleRun} disabled={executing}>
          {executing ? 'Running…' : '▶ Run Script'}
        </button>
        <button className={styles.copyButton} onClick={handleCopy}>
          {copied ? '✓ Copied' : 'Copy Script'}
        </button>
      </div>
    </div>
  );
};
