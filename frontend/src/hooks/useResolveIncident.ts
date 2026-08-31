import { useState } from 'react';
import { AgentResponse, StreamEvent } from '../types/incident';
import { api } from '../services/api';

export interface AgentStatus {
  agent: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
}

export const useResolveIncident = () => {
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingSummary, setStreamingSummary] = useState<string>('');
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
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

  const resolveIncidentStream = async (incidentId: string, userQuery: string) => {
    try {
      setLoading(true);
      setIsStreaming(true);
      setError(null);
      setStreamingSummary('');
      setResponse(null);
      setAgentStatuses({
        servicenow: { agent: 'servicenow', agent_name: 'ServiceNow Agent', status: 'pending' },
        confluence: { agent: 'confluence', agent_name: 'Knowledge Base Agent', status: 'pending' },
        change: { agent: 'change', agent_name: 'Change Correlation Agent', status: 'pending' },
        logs: { agent: 'logs', agent_name: 'Logs Agent', status: 'pending' },
        events: { agent: 'events', agent_name: 'Events Agent', status: 'pending' },
        remediation: { agent: 'remediation', agent_name: 'Remediation Agent', status: 'pending' },
        synthesis: { agent: 'synthesis', agent_name: 'Synthesis', status: 'pending' },
      });

      let accumulatedSummary = '';

      await api.resolveStream(
        { incident_id: incidentId, user_query: userQuery },
        (eventData: StreamEvent) => {
          if (eventData.event === 'agent_start') {
            setAgentStatuses((prev) => ({
              ...prev,
              [eventData.agent]: {
                agent: eventData.agent,
                agent_name: eventData.agent_name || eventData.agent,
                status: 'running',
              },
            }));
          } else if (eventData.event === 'agent_complete') {
            setAgentStatuses((prev) => ({
              ...prev,
              [eventData.agent]: {
                agent: eventData.agent,
                agent_name: eventData.agent_name || eventData.agent,
                status: 'completed',
                result: eventData.result,
              },
            }));
          } else if (eventData.event === 'synthesis_start') {
            setAgentStatuses((prev) => ({
              ...prev,
              synthesis: {
                agent: 'synthesis',
                agent_name: 'Synthesis',
                status: 'running',
              },
            }));
          } else if (eventData.event === 'llm_chunk') {
            accumulatedSummary += eventData.content || '';
            setStreamingSummary(accumulatedSummary);
          } else if (eventData.event === 'complete') {
            setResponse(eventData.result);
            setAgentStatuses((prev) => ({
              ...prev,
              synthesis: {
                ...prev.synthesis,
                status: 'completed',
              },
            }));
          } else if (eventData.event === 'error') {
            setError(eventData.detail || 'Resolution streaming failed');
          }
        },
        (finalResult) => {
          setIsStreaming(false);
          setLoading(false);
          if (finalResult) {
            setResponse(finalResult);
          }
        },
        (err) => {
          setIsStreaming(false);
          setLoading(false);
          const errorMessage = err.message || 'Failed to resolve incident stream';
          setError(errorMessage);
        }
      );
    } catch (err) {
      setIsStreaming(false);
      setLoading(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to resolve incident stream';
      setError(errorMessage);
      throw err;
    }
  };

  return {
    response,
    loading,
    isStreaming,
    streamingSummary,
    agentStatuses,
    error,
    resolveIncident,
    resolveIncidentStream,
  };
};
