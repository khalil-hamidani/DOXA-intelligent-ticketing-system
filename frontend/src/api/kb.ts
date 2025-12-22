import api from './client';
import { KBDocument, KBSnippet } from '../types';

export const kbApi = {
  // Get all documents
  getDocuments: async (category?: string): Promise<KBDocument[]> => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    
    const response = await api.get<KBDocument[]>(`/kb/documents?${params.toString()}`);
    return response.data;
  },

  // Get single document
  getDocument: async (docId: string): Promise<KBDocument> => {
    const response = await api.get<KBDocument>(`/kb/documents/${docId}`);
    return response.data;
  },

  // Create document
  createDocument: async (data: { title: string; content: string; category?: string }): Promise<KBDocument> => {
    const response = await api.post<KBDocument>('/kb/documents', data);
    return response.data;
  },

  // Update document (Note: backend may not have this endpoint)
  updateDocument: async (docId: string, data: { title?: string; content?: string; category?: string }): Promise<KBDocument> => {
    const response = await api.put<KBDocument>(`/kb/documents/${docId}`, data);
    return response.data;
  },

  // Delete document (Note: backend may not have this endpoint)
  deleteDocument: async (docId: string): Promise<void> => {
    await api.delete(`/kb/documents/${docId}`);
  },

  // Get all snippets
  getSnippets: async (): Promise<KBSnippet[]> => {
    const response = await api.get<KBSnippet[]>('/kb/snippets');
    return response.data;
  },
};
