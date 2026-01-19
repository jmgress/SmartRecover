import { useState } from 'react';
import { api } from '../services/api';
import { Incident } from '../types/incident';

interface UseUpdateIncidentStatusResult {
  updateStatus: (incidentId: string, newStatus: string) => Promise<void>;
  isUpdating: boolean;
  error: string | null;
}

export const useUpdateIncidentStatus = (
  onSuccess?: (incident: Incident) => void,
  onError?: (error: Error) => void
): UseUpdateIncidentStatusResult => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateStatus = async (incidentId: string, newStatus: string) => {
    setIsUpdating(true);
    setError(null);

    try {
      const updatedIncident = await api.updateIncidentStatus(incidentId, newStatus);
      onSuccess?.(updatedIncident);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update status';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
      throw err;
    } finally {
      setIsUpdating(false);
    }
  };

  return { updateStatus, isUpdating, error };
};
