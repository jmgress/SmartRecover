import { useState } from 'react';
import { AgentResponse } from '../types/incident';
import { api } from '../services/api';

export const useResolveIncident = () => {
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const resolveIncident = async (incidentId: string, userQuery: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.resolveIncident({
        incident_id: incidentId,
        user_query: userQuery,
      });
      setResponse(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resolve incident';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { response, loading, error, resolveIncident };
};
