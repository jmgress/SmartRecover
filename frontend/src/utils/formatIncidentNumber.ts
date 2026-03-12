/** Format incident ID to ServiceNow-style 7-digit number (e.g., INC001 → INC0000001) */
export function formatIncidentNumber(id: string): string {
  const match = id.match(/^([A-Z]+)(\d+)$/);
  if (match) {
    return `${match[1]}${match[2].padStart(7, '0')}`;
  }
  return id;
}
