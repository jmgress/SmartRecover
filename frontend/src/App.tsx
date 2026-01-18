import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatContainer } from './components/ChatContainer';
import { ChatInput } from './components/ChatInput';
import { useIncidents } from './hooks/useIncidents';
import { useResolveIncident } from './hooks/useResolveIncident';
import { AgentResponse } from './types/incident';
import './App.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
}

function App() {
  const { incidents, loading: incidentsLoading } = useIncidents();
  const { resolveIncident, loading: resolving } = useResolveIncident();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSelectIncident = (id: string) => {
    setSelectedIncidentId(id);
    setMessages([]);
  };

  const handleSubmitQuery = async (query: string) => {
    if (!selectedIncidentId) return;

    setMessages((prev) => [...prev, { content: query, isUser: true }]);

    try {
      const response = await resolveIncident(selectedIncidentId, query);
      setMessages((prev) => [...prev, { content: response, isUser: false }]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setMessages((prev) => [...prev, { content: `Error: ${errorMessage}`, isUser: false }]);
    }
  };

  if (incidentsLoading) {
    return <div className="loading-screen">Loading incidents...</div>;
  }

  return (
    <div className="App">
      <Sidebar
        incidents={incidents}
        selectedIncidentId={selectedIncidentId}
        onSelectIncident={handleSelectIncident}
      />
      <div className="main">
        <ChatContainer messages={messages} selectedIncidentId={selectedIncidentId} />
        <ChatInput
          onSubmit={handleSubmitQuery}
          disabled={!selectedIncidentId}
          loading={resolving}
        />
      </div>
    </div>
  );
}

export default App;
