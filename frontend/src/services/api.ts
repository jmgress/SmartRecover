import { Incident, IncidentQuery, AgentResponse, LLMTestResponse } from '../types/incident';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  incident_id: string;
  message: string;
  conversation_history: ChatMessage[];
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
};
