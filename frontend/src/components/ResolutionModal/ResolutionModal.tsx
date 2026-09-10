import React, { useCallback, useState } from 'react';
import { api } from '../../services/api';
import { Incident, ResolutionGrade } from '../../types/incident';
import styles from './ResolutionModal.module.css';

interface ResolutionModalProps {
  incident: Incident;
  onClose: () => void;
  onResolved: (updatedIncident: Incident) => void;
}

export const ResolutionModal: React.FC<ResolutionModalProps> = ({
  incident,
  onClose,
  onResolved,
}) => {
  const [resolutionText, setResolutionText] = useState('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [grade, setGrade] = useState<ResolutionGrade | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateDraft = useCallback(async () => {
    setIsDrafting(true);
    setError(null);
    try {
      const response = await api.draftResolution(incident.id);
      setResolutionText(response.draft);
      setGrade(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate draft');
    } finally {
      setIsDrafting(false);
    }
  }, [incident.id]);

  const handleSubmit = useCallback(async () => {
    if (!resolutionText.trim()) {
      setError('Enter a resolution before submitting.');
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await api.submitResolution(incident.id, resolutionText.trim());
      setGrade(response.grade);
      if (response.grade.passed) {
        onResolved({ ...incident, status: 'resolved' });
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit resolution');
    } finally {
      setIsSubmitting(false);
    }
  }, [incident, resolutionText, onResolved, onClose]);

  const busy = isDrafting || isSubmitting;

  return (
    <div className={styles.overlay} role="presentation" onClick={onClose}>
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="resolution-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <h2 id="resolution-modal-title">Resolve incident {incident.id}</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <p className={styles.hint}>
          Describe the root cause, the actions taken, and how the fix was verified. The
          resolution is graded by AI against what was recorded for this incident — generic
          text like “resolved” will be rejected.
        </p>

        <textarea
          className={styles.textarea}
          value={resolutionText}
          onChange={(e) => setResolutionText(e.target.value)}
          placeholder="Root cause, actions taken, verification…"
          rows={8}
          disabled={busy}
          aria-label="Resolution text"
        />

        {grade && !grade.passed && (
          <div className={styles.gradeFailed} role="alert">
            <strong>
              Resolution rejected (score {Math.round(grade.score * 100)}%, needs{' '}
              {Math.round(grade.threshold * 100)}%)
            </strong>
            <p>{grade.feedback}</p>
            {grade.issues.length > 0 && (
              <ul>
                {grade.issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {error && (
          <div className={styles.error} role="alert">
            {error}
          </div>
        )}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.draftButton}
            onClick={handleGenerateDraft}
            disabled={busy}
          >
            {isDrafting ? 'Generating draft…' : 'Generate AI draft'}
          </button>
          <div className={styles.rightActions}>
            <button type="button" className={styles.cancelButton} onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button
              type="button"
              className={styles.submitButton}
              onClick={handleSubmit}
              disabled={busy || !resolutionText.trim()}
            >
              {isSubmitting ? 'Grading…' : 'Submit resolution'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
