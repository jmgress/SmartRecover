import { Incident, IncidentQuery, AgentResponse } from '../types/incident';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

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
};
