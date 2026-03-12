import { formatIncidentNumber } from './formatIncidentNumber';

describe('formatIncidentNumber', () => {
  it('pads a short incident number to 7 digits', () => {
    expect(formatIncidentNumber('INC001')).toBe('INC0000001');
  });

  it('pads a medium-length incident number to 7 digits', () => {
    expect(formatIncidentNumber('INC1234')).toBe('INC0001234');
  });

  it('does not pad a number that is already 7 digits', () => {
    expect(formatIncidentNumber('INC0000001')).toBe('INC0000001');
  });

  it('does not alter a number that is longer than 7 digits', () => {
    expect(formatIncidentNumber('INC00000001')).toBe('INC00000001');
  });

  it('returns the original string when it does not match the expected pattern', () => {
    expect(formatIncidentNumber('UNKNOWN')).toBe('UNKNOWN');
  });

  it('works with prefixes other than INC', () => {
    expect(formatIncidentNumber('PRB001')).toBe('PRB0000001');
  });
});
