import React from 'react';
import { render, screen } from '@testing-library/react';
import { IncidentItem } from './IncidentItem';

describe('IncidentItem', () => {
  it('falls back to keyword-derived category when backend category is empty', () => {
    render(
      <IncidentItem
        incident={{
          id: 'INC024',
          title: 'Database connection timeout',
          description: 'Connections are timing out',
          severity: 'medium',
          status: 'open',
          created_at: '2026-01-14T09:39:56.376226Z',
          affected_services: ['user-service'],
          assignee: 'search-team',
          category: null,
        }}
        isActive={false}
        onClick={() => {}}
      />
    );

    expect(screen.getAllByText('Database').length).toBeGreaterThan(0);
  });
});
