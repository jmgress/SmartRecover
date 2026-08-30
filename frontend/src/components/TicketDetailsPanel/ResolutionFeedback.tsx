import React, { useState } from 'react';
import { api } from '../../services/api';
import styles from './ResolutionFeedback.module.css';

interface ResolutionFeedbackProps {
  incidentId: string;
}

export const ResolutionFeedback: React.FC<ResolutionFeedbackProps> = ({ incidentId }) => {
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitFeedback = async (selectedRating: 'helpful' | 'not_helpful') => {
    setSubmitting(true);
    setError(null);
    try {
      await api.submitFeedback({
        incident_id: incidentId,
        rating: selectedRating,
        comment: comment || undefined,
      });
      setSubmitted(true);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return <p className={styles.confirmation} aria-live="polite">Thanks for your feedback.</p>;
  }

  return (
    <section className={styles.container} aria-label="Resolution feedback">
      <h4 className={styles.title}>Was this resolution helpful?</h4>
      <textarea
        className={styles.comment}
        aria-label="Optional feedback comment"
        value={comment}
        onChange={(event) => setComment(event.target.value)}
        maxLength={2000}
        placeholder="Optional comment"
      />
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.helpful}
          onClick={() => submitFeedback('helpful')}
          disabled={submitting}
        >
          Helpful
        </button>
        <button
          type="button"
          className={styles.notHelpful}
          onClick={() => submitFeedback('not_helpful')}
          disabled={submitting}
        >
          Not helpful
        </button>
      </div>
      {error && <p className={styles.error} role="alert">{error}</p>}
    </section>
  );
};
