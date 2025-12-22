export type UserRole = 'CLIENT' | 'AGENT' | 'ADMIN';
export type TicketStatus = 'OPEN' | 'AI_ANSWERED' | 'ESCALATED' | 'CLOSED';
export type ResponseSource = 'AI' | 'HUMAN';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  language: string;
  is_active: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface Ticket {
  id: string;
  reference: string;
  subject: string;
  description: string;
  category: string | null;
  status: TicketStatus;
  client_id: number;
  assigned_agent_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface TicketResponse {
  id: string;
  source: ResponseSource;
  content: string;
  created_at: string;
}

export interface TicketDetail extends Ticket {
  responses: TicketResponse[];
}

export interface Feedback {
  id: string;
  ticket_id: string;
  rating: number;
  satisfied: boolean;
  comment: string | null;
  created_at: string;
}

export interface KBDocument {
  id: string;
  title: string;
  content: string;
  category: string | null;
  created_at: string;
}

export interface KBSnippet {
  id: string;
  doc_id: string;
  content: string;
  relevance_score: number | null;
}

export interface MetricsOverview {
  total_tickets: number;
  ai_resolution_rate: number;
  avg_response_time_minutes: number;
  avg_satisfaction_rating: number;
  tickets_by_status: Record<string, number>;
  tickets_by_category: Record<string, number>;
}
