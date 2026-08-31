import { api } from './api';

global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('healthCheck', () => {
    it('should return health status', async () => {
      const mockResponse = { status: 'healthy', service: 'incident-resolver' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.healthCheck();
      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/health'));
    });

    it('should throw error on failed health check', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false });

      await expect(api.healthCheck()).rejects.toThrow('Health check failed');
    });
  });

  describe('getIncidents', () => {
    it('should fetch all incidents', async () => {
      const mockIncidents = [
        { id: 'INC001', title: 'Test' },
        { id: 'INC002', title: 'Test 2' },
      ];
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockIncidents,
      });

      const result = await api.getIncidents();
      expect(result).toEqual(mockIncidents);
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/incidents'));
    });

    it('should throw error on failed fetch', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false });

      await expect(api.getIncidents()).rejects.toThrow('Failed to fetch incidents');
    });
  });

  describe('getIncident', () => {
    it('should fetch a specific incident', async () => {
      const mockIncident = { id: 'INC001', title: 'Test' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockIncident,
      });

      const result = await api.getIncident('INC001');
      expect(result).toEqual(mockIncident);
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/incidents/INC001'));
    });
  });

  describe('resolveIncident', () => {
    it('should resolve an incident', async () => {
      const mockResponse = {
        incident_id: 'INC001',
        resolution_steps: ['Step 1'],
        related_knowledge: [],
        correlated_changes: [],
        summary: 'Test',
        confidence: 0.9,
      };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.resolveIncident({
        incident_id: 'INC001',
        user_query: 'How to fix?',
      });
      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/resolve'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  describe('resolveStream', () => {
    it('should stream resolution events and complete', async () => {
      const events: any[] = [];
      let completeResult: any = null;
      let isCompleted = false;

      const mockStreamData = [
        'data: {"event": "agent_start", "agent": "servicenow", "agent_name": "ServiceNow Agent"}\n\n',
        'data: {"event": "agent_complete", "agent": "servicenow", "agent_name": "ServiceNow Agent", "result": {}}\n\n',
        'data: {"event": "synthesis_start", "agent": "synthesis", "agent_name": "Synthesis"}\n\n',
        'data: {"event": "llm_chunk", "content": "Resolution summary"}\n\n',
        'data: {"event": "complete", "result": {"incident_id": "INC001", "summary": "Resolution summary", "resolution_steps": [], "related_knowledge": [], "correlated_changes": [], "confidence": 0.9}}\n\n',
        'data: [DONE]\n\n',
      ];

      let streamIndex = 0;
      const mockReader = {
        read: jest.fn().mockImplementation(async () => {
          if (streamIndex < mockStreamData.length) {
            const chunk = Buffer.from(mockStreamData[streamIndex++]);
            return { done: false, value: chunk };
          }
          return { done: true, value: undefined };
        }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      await api.resolveStream(
        { incident_id: 'INC001', user_query: 'Fix' },
        (e) => events.push(e),
        (result) => {
          isCompleted = true;
          completeResult = result;
        },
        () => {}
      );

      expect(events.length).toBe(5);
      expect(events[0].event).toBe('agent_start');
      expect(isCompleted).toBe(true);
      expect(completeResult?.summary).toBe('Resolution summary');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/resolve/stream'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('submitFeedback', () => {
    it('should submit resolution feedback', async () => {
      const mockResponse = {
        id: 'feedback-1',
        incident_id: 'INC001',
        rating: 'helpful',
        comment: 'Worked',
        created_at: '2026-08-30T00:00:00Z',
      };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      await expect(api.submitFeedback({
        incident_id: 'INC001',
        rating: 'helpful',
        comment: 'Worked',
      })).resolves.toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/feedback'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            incident_id: 'INC001',
            rating: 'helpful',
            comment: 'Worked',
          }),
        })
      );
    });
  });
});
