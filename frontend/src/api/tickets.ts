import api from './client';
import { Ticket, TicketDetail, TicketResponse, Feedback, TicketStatus } from '../types';

interface TicketFilters {
  skip?: number;
  limit?: number;
  status?: TicketStatus | string;
  category?: string;
}

interface FeedbackData {
  rating: number;
  comment?: string;
}

export const ticketsApi = {
  // Get all tickets (filters by role on backend - clients see their own, agents/admins see all)
  getAllTickets: async (filters: TicketFilters = {}): Promise<Ticket[]> => {
    const params = new URLSearchParams();
    if (filters.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters.limit !== undefined) params.append('limit', String(filters.limit));
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    
    const response = await api.get<Ticket[]>(`/tickets/?${params.toString()}`);
    return response.data;
  },

  // Get client's own tickets (same endpoint, backend filters by user role)
  getMyTickets: async (filters: TicketFilters = {}): Promise<Ticket[]> => {
    const params = new URLSearchParams();
    if (filters.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters.limit !== undefined) params.append('limit', String(filters.limit));
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    
    const response = await api.get<Ticket[]>(`/tickets/?${params.toString()}`);
    return response.data;
  },

  // Get single ticket details
  getTicket: async (ticketId: string): Promise<TicketDetail> => {
    const response = await api.get<TicketDetail>(`/tickets/${ticketId}`);
    return response.data;
  },

  // Create new ticket (note trailing slash to avoid redirect)
  createTicket: async (data: { subject: string; description: string; category?: string }): Promise<Ticket> => {
    const response = await api.post<Ticket>('/tickets/', data);
    return response.data;
  },

  // Add response to ticket
  addResponse: async (ticketId: string, content: string): Promise<TicketResponse> => {
    const response = await api.post<TicketResponse>(`/tickets/${ticketId}/reply`, { content });
    return response.data;
  },

  // Escalate ticket
  escalateTicket: async (ticketId: string): Promise<Ticket> => {
    const response = await api.post<Ticket>(`/tickets/${ticketId}/escalate`);
    return response.data;
  },

  // Close ticket
  closeTicket: async (ticketId: string): Promise<Ticket> => {
    const response = await api.post<Ticket>(`/tickets/${ticketId}/close`);
    return response.data;
  },

  // Submit feedback
  submitFeedback: async (ticketId: string, data: FeedbackData): Promise<Feedback> => {
    const response = await api.post<Feedback>(`/tickets/${ticketId}/feedback`, data);
    return response.data;
  },

  // Get feedback
  getFeedback: async (ticketId: string): Promise<Feedback[]> => {
    const response = await api.get<Feedback[]>(`/tickets/${ticketId}/feedback`);
    return response.data;
  },
};
