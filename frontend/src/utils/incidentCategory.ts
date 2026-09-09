import { Incident, IncidentCategory } from '../types/incident';

const DEFAULT_CATEGORY: IncidentCategory = 'Application';

const CATEGORY_RULES: Array<{ name: IncidentCategory; keywords: string[] }> = [
  { name: 'Database', keywords: ['database', 'replica lag', 'connection timeout'] },
  { name: 'Application', keywords: ['memory leak'] },
  { name: 'Infrastructure', keywords: ['kubernetes', 'container', 'load balancer', 'service mesh'] },
  { name: 'Network', keywords: ['network', 'latency'] },
  { name: 'Security', keywords: ['ssl', 'certificate', 'oauth'] },
  { name: 'Storage', keywords: ['disk', 'storage'] },
  { name: 'Monitoring', keywords: ['log', 'elasticsearch'] },
  { name: 'Cache', keywords: ['cache', 'redis', 'cdn'] },
  { name: 'Payments', keywords: ['payment'] },
  { name: 'API', keywords: ['api'] },
];

export function getCategory(title: string): IncidentCategory {
  const haystack = title.toLowerCase();
  for (const rule of CATEGORY_RULES) {
    if (rule.keywords.some((keyword) => haystack.includes(keyword))) {
      return rule.name;
    }
  }

  return DEFAULT_CATEGORY;
}

export function getIncidentCategory(incident: Pick<Incident, 'title' | 'category'>): string {
  return incident.category ?? getCategory(incident.title);
}
