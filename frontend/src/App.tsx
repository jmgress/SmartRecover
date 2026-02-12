import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { TicketDetailsPanel } from './components/TicketDetailsPanel';
import { Admin } from './components/Admin';
import { Header } from './components/Header';
import { Resizer } from './components/Resizer';
import { IncidentStatusFilter } from './components/FilterButtons';
import { useIncidents } from './hooks/useIncidents';
import { AgentResponse, TicketDetails, Incident } from './types/incident';
import { api, ChatMessage as APIChatMessage } from './services/api';
import './App.css';

interface ChatMessage {
  content: string | AgentResponse;
  isUser: boolean;
  isStreaming?: boolean;
}

function App() {
  const { incidents, loading: incidentsLoading, refetch: refetchIncidents } = useIncidents();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [ticketDetails, setTicketDetails] = useState<TicketDetails | null>(null);
  const [loadingTicketDetails, setLoadingTicketDetails] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [retrieving, setRetrieving] = useState(false);
  const [retrieveError, setRetrieveError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<IncidentStatusFilter>(() => {
    // Load filter from localStorage, default to 'open'
    const saved = localStorage.getItem('incidentFilter');
    const validFilters: IncidentStatusFilter[] = ['open', 'investigating', 'closed'];
    return saved && validFilters.includes(saved as IncidentStatusFilter) 
      ? (saved as IncidentStatusFilter) 
      : 'open';
  });

  // Panel width state - load from localStorage or use defaults
  const [middlePanelWidth, setMiddlePanelWidth] = useState<number>(() => {
    const saved = localStorage.getItem('middlePanelWidth');
    return saved ? parseInt(saved, 10) : 50; // Default 50% of available space
  });

  // Persist panel width to localStorage
  useEffect(() => {
    localStorage.setItem('middlePanelWidth', middlePanelWidth.toString());
  }, [middlePanelWidth]);

  // Persist filter to localStorage
  useEffect(() => {
    localStorage.setItem('incidentFilter', activeFilter);
  }, [activeFilter]);

  // Handle panel resize
  const handleResize = (deltaX: number) => {
    // Get the container width (excluding sidebar)
    const appElement = document.querySelector('.App');
    if (!appElement) return;
    
    const containerWidth = appElement.clientWidth - 280; // Subtract sidebar width
    const deltaPercent = (deltaX / containerWidth) * 100;
    
    // Update width with constraints (min 30%, max 70%)
    setMiddlePanelWidth(prev => {
      const newWidth = prev + deltaPercent;
      return Math.max(30, Math.min(70, newWidth));
    });
  };

  // Filter incidents based on active filter
  const filteredIncidents = incidents.filter((incident: Incident) => {
    if (activeFilter === 'open') {
      return incident.status === 'open';
    } else if (activeFilter === 'investigating') {
      return incident.status === 'investigating';
    } else if (activeFilter === 'closed') {
      return incident.status === 'resolved';
    }
    return false;
  });

  const handleFilterChange = (filter: IncidentStatusFilter) => {
    setActiveFilter(filter);
  };

  const handleSelectIncident = async (id: string) => {
    setSelectedIncidentId(id);
    setMessages([]);
    setShowAdmin(false);
    setRetrieveError(null);
    
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

  const handleIncidentUpdate = (updatedIncident: Incident) => {
    // Update the ticket details with the new incident data
    if (ticketDetails) {
      setTicketDetails({
        ...ticketDetails,
        incident: updatedIncident,
      });
    }
    // Refresh the incidents list to show updated status in sidebar
    refetchIncidents();
  };

  const handleRetrieve = async () => {
    if (!selectedIncidentId) return;
    
    setRetrieving(true);
    setRetrieveError(null);
    
    try {
      const agentResults = await api.retrieveIncidentContext(selectedIncidentId);
      
      // Update ticket details with the retrieved agent results
      if (ticketDetails) {
        setTicketDetails({
          ...ticketDetails,
          agent_results: agentResults,
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to retrieve context';
      setRetrieveError(errorMessage);
      console.error('Failed to retrieve incident context:', error);
    } finally {
      setRetrieving(false);
    }
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
      <Header onShowAdmin={handleShowAdmin} showingAdmin={showAdmin} />
      <div className="App-content">
        <Sidebar
          incidents={filteredIncidents}
          selectedIncidentId={selectedIncidentId}
          onSelectIncident={handleSelectIncident}
          onShowAdmin={handleShowAdmin}
          showingAdmin={showAdmin}
          activeFilter={activeFilter}
          onFilterChange={handleFilterChange}
        />
        {showAdmin ? (
          <div className="admin-container">
            <Admin />
          </div>
        ) : (
          <>
            <div 
              className="middle-panel"
              style={{ width: `${middlePanelWidth}%` }}
            >
              <TicketDetailsPanel 
                ticketDetails={ticketDetails}
                loading={loadingTicketDetails}
                onIncidentUpdate={handleIncidentUpdate}
                onRetrieve={handleRetrieve}
                retrieving={retrieving}
                retrieveError={retrieveError}
              />
            </div>
            <Resizer onResize={handleResize} />
            <div 
              className="right-panel"
              style={{ width: `${100 - middlePanelWidth}%` }}
            >
              <ChatPanel
                messages={messages}
                selectedIncidentId={selectedIncidentId}
                onSubmitQuery={handleSubmitQuery}
                isStreaming={isStreaming}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
