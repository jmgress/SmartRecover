export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
  updated_at?: string;
  affected_services: string[];
  assignee?: string;
}

export interface IncidentQuery {
  incident_id: string;
  user_query: string;
}

export interface AgentResponse {
  incident_id: string;
  resolution_steps: string[];
  related_knowledge: string[];
  correlated_changes: string[];
  summary: string;
  confidence: number;
}
