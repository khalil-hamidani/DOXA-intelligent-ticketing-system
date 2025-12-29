export const API_BASE_URL = 'http://192.168.1.36:8000/api/v1';

export const TICKET_STATUS = {
  OPEN: 'OPEN',
  AI_ANSWERED: 'AI_ANSWERED',
  ESCALATED: 'ESCALATED',
  CLOSED: 'CLOSED',
} as const;

export const USER_ROLES = {
  CLIENT: 'CLIENT',
  AGENT: 'AGENT',
  ADMIN: 'ADMIN',
} as const;

export const STATUS_COLORS: Record<string, string> = {
  OPEN: 'bg-green-100 text-green-800',
  AI_ANSWERED: 'bg-blue-100 text-blue-800',
  ESCALATED: 'bg-orange-100 text-orange-800',
  CLOSED: 'bg-gray-100 text-gray-800',
};

export const CATEGORIES = ['TECHNICAL', 'BILLING', 'OTHER'];

export const TICKET_CATEGORIES: Record<string, string> = {
  TECHNICAL: 'Technical Support',
  BILLING: 'Billing & Payments',
  OTHER: 'General Inquiry',
};

export const KB_CATEGORIES: Record<string, string> = {
  TECHNICAL: 'Technical',
  BILLING: 'Billing',
  GENERAL: 'General',
  FAQ: 'FAQ',
};
