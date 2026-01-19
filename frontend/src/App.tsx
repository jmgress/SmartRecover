import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { TicketDetailsPanel } from './components/TicketDetailsPanel';
import { Admin } from './components/Admin';
import { useIncidents } from './hooks/useIncidents';
import { useResolveIncident } from './hooks/useResolveIncident';
import { AgentResponse, TicketDetails } from './types/incident';
import { api, ChatMessage as APIChatMessage } from './services/api';
import './App.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

function App() {
  const { incidents, loading: incidentsLoading } = useIncidents();
  const { resolveIncident, loading: resolving } = useResolveIncident();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [ticketDetails, setTicketDetails] = useState<TicketDetails | null>(null);
  const [loadingTicketDetails, setLoadingTicketDetails] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSelectIncident = async (id: string) => {
    setSelectedIncidentId(id);
    setMessages([]);
    setShowAdmin(false);
    
    // Fetch ticket details
    setLoadingTicketDetails(true);
    try {
      const details = await api.getIncidentDetails(id);
      setTicketDetails(details);
    } catch (error) {
      console.error('Failed to fetch ticket details:', error);
      setTicketDetails(null);
    } finally {
      setLoadingTicketDetails(false);
    }
  };

  const handleShowAdmin = () => {
    setShowAdmin(true);
    setSelectedIncidentId(null);
    setTicketDetails(null);
  };

  const handleSubmitQuery = async (query: string) => {
    if (!selectedIncidentId) return;

    // Add user message
    setMessages((prev) => [...prev, { content: query, isUser: true }]);

    // Build conversation history for API
    const conversationHistory: APIChatMessage[] = messages
      .filter(msg => typeof msg.content === 'string')
      .map(msg => ({
        role: msg.isUser ? 'user' as const : 'assistant' as const,
        content: msg.content as string,
      }));

    // Add placeholder for assistant's streaming response
    const streamingMessageIndex = messages.length + 1;
    setMessages((prev) => [...prev, { content: '', isUser: false, isStreaming: true }]);
    setIsStreaming(true);

    let accumulatedContent = '';

    try {
      await api.chatStream(
        {
          incident_id: selectedIncidentId,
          message: query,
          conversation_history: conversationHistory,
        },
        // onChunk
        (chunk: string) => {
          accumulatedContent += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[streamingMessageIndex] = {
              content: accumulatedContent,
              isUser: false,
              isStreaming: true,
            };
            return updated;
          });
        },
        // onComplete
        () => {
          setIsStreaming(false);
          setMessages((prev) => {
            const updated = [...prev];
            updated[streamingMessageIndex] = {
              content: accumulatedContent,
              isUser: false,
              isStreaming: false,
            };
            return updated;
          });
          
          // Refresh ticket details to get updated agent results
          if (selectedIncidentId) {
            api.getIncidentDetails(selectedIncidentId)
              .then(details => setTicketDetails(details))
              .catch(err => console.error('Failed to refresh ticket details:', err));
          }
        },
        // onError
        (error: Error) => {
          setIsStreaming(false);
          const errorMessage = `Error: ${error.message}`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[streamingMessageIndex] = {
              content: errorMessage,
              isUser: false,
              isStreaming: false,
            };
            return updated;
          });
        }
      );
    } catch (error) {
      setIsStreaming(false);
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
        onShowAdmin={handleShowAdmin}
        showingAdmin={showAdmin}
      />
      {showAdmin ? (
        <div className="admin-container">
          <Admin />
        </div>
      ) : (
        <>
          <TicketDetailsPanel 
            ticketDetails={ticketDetails}
            loading={loadingTicketDetails}
          />
          <ChatPanel
            messages={messages}
            selectedIncidentId={selectedIncidentId}
            onSubmitQuery={handleSubmitQuery}
            isStreaming={isStreaming}
          />
        </>
      )}
    </div>
  );
}

export default App;
