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
});
