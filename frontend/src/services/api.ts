import { Incident, IncidentQuery, AgentResponse, LLMTestResponse, LLMConfigResponse, LoggingConfigResponse, UpdateLoggingConfigRequest } from '../types/incident';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  incident_id: string;
  message: string;
  conversation_history: ChatMessage[];
  excluded_items?: string[];
}

export interface ExcludeItemRequest {
  item_id: string;
  item_type: string;
  source: string;
}

export const api = {
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  },

  async getIncidents(): Promise<Incident[]> {
    const response = await fetch(`${API_BASE_URL}/incidents`);
    if (!response.ok) {
      throw new Error('Failed to fetch incidents');
    }
    return response.json();
  },

  async getIncident(id: string): Promise<Incident> {
    const response = await fetch(`${API_BASE_URL}/incidents/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch incident ${id}`);
    }
    return response.json();
  },

  async updateIncidentStatus(id: string, status: string): Promise<Incident> {
    const response = await fetch(`${API_BASE_URL}/incidents/${id}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update incident status');
    }
    return response.json();
  },

  async getIncidentDetails(id: string): Promise<import('../types/incident').TicketDetails> {
    const response = await fetch(`${API_BASE_URL}/incidents/${id}/details`);
    if (!response.ok) {
      throw new Error(`Failed to fetch incident details ${id}`);
    }
    return response.json();
  },

  async resolveIncident(query: IncidentQuery): Promise<AgentResponse> {
    const response = await fetch(`${API_BASE_URL}/resolve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });
    if (!response.ok) {
      throw new Error('Failed to resolve incident');
    }
    return response.json();
  },

  async testLLM(message: string): Promise<LLMTestResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/test-llm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      throw new Error('Failed to test LLM');
    }
    return response.json();
  },

  async getLLMConfig(): Promise<LLMConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/llm-config`);
    if (!response.ok) {
      throw new Error('Failed to fetch LLM configuration');
    }
    return response.json();
  },

  async getLoggingConfig(): Promise<LoggingConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/logging-config`);
    if (!response.ok) {
      throw new Error('Failed to fetch logging configuration');
    }
    return response.json();
  },

  async updateLoggingConfig(config: UpdateLoggingConfigRequest): Promise<LoggingConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/logging-config`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update logging configuration');
    }
    return response.json();
  },

  async retrieveIncidentContext(id: string): Promise<import('../types/incident').AgentResults> {
    const response = await fetch(`${API_BASE_URL}/incidents/${id}/retrieve-context`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to retrieve incident context');
    }
    return response.json();
  },

  /**
   * Stream a chat response using Server-Sent Events.
   * @param request The chat request
   * @param onChunk Callback for each chunk received
   * @param onComplete Callback when streaming is complete
   * @param onError Callback for errors
   */
  async chatStream(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to start chat stream: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete();
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            
            if (data === '[DONE]') {
              onComplete();
              return;
            }
            
            if (data.trim()) {
              onChunk(data);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  },

  async getAgentPrompts(): Promise<import('../types/incident').AgentPromptsResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/agent-prompts`);
    if (!response.ok) {
      throw new Error('Failed to fetch agent prompts');
    }
    return response.json();
  },

  async updateAgentPrompt(agentName: string, prompt: string): Promise<import('../types/incident').AgentPromptInfo> {
    const response = await fetch(`${API_BASE_URL}/admin/agent-prompts/${agentName}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update agent prompt');
    }
    return response.json();
  },

  async resetAgentPrompts(agentName?: string): Promise<{ message: string }> {
    const url = agentName 
      ? `${API_BASE_URL}/admin/agent-prompts/reset?agent_name=${agentName}`
      : `${API_BASE_URL}/admin/agent-prompts/reset`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reset agent prompts');
    }
    return response.json();
  },

  async excludeItem(incidentId: string, request: ExcludeItemRequest): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/exclude-item`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to exclude item');
    }
    return response.json();
  },

  async getExcludedItems(incidentId: string): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/excluded-items`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get excluded items');
    }
    return response.json();
  },

  async unexcludeItem(incidentId: string, itemId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/excluded-items/${encodeURIComponent(itemId)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to un-exclude item');
    }
    return response.json();
  },

  async getAccuracyMetrics(): Promise<import('../types/incident').AccuracyMetricsResponse> {
    const response = await fetch(`${API_BASE_URL}/admin/accuracy-metrics`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get accuracy metrics');
    }
    return response.json();
  },

  async getPromptLogs(incidentId?: string, limit?: number): Promise<import('../types/incident').PromptLogsResponse> {
    const params = new URLSearchParams();
    if (incidentId) {
      params.append('incident_id', incidentId);
    }
    if (limit) {
      params.append('limit', limit.toString());
    }
    
    const url = `${API_BASE_URL}/admin/prompt-logs${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch prompt logs');
    }
    return response.json();
  },

  async clearPromptLogs(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/admin/prompt-logs`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to clear prompt logs');
    }
    return response.json();
  },
};
