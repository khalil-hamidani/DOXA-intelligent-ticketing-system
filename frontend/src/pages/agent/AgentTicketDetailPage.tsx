import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { TicketDetail, Feedback } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';

export const AgentTicketDetailPage: React.FC = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchTicket = async () => {
    if (!ticketId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await ticketsApi.getTicket(ticketId);
      setTicket(data);
      // Try to get feedback
      try {
        const fbData = await ticketsApi.getFeedback(ticketId);
        setFeedback(fbData || []);
      } catch {
        // No feedback yet
      }
    } catch {
      setError('Failed to load ticket details');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketId || !replyContent.trim()) return;
    
    setIsSubmitting(true);
    try {
      await ticketsApi.addResponse(ticketId, replyContent);
      setReplyContent('');
      fetchTicket();
    } catch {
      alert('Failed to send reply');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseTicket = async () => {
    if (!ticketId) return;
    if (!confirm('Are you sure you want to close this ticket?')) return;
    
    try {
      await ticketsApi.closeTicket(ticketId);
      fetchTicket();
    } catch {
      alert('Failed to close ticket');
    }
  };

  const handleEscalate = async () => {
    if (!ticketId) return;
    try {
      await ticketsApi.escalateTicket(ticketId);
      fetchTicket();
    } catch {
      alert('Failed to escalate ticket');
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  if (error || !ticket) {
    return (
      <Layout>
        <ErrorMessage message={error || 'Ticket not found'} onRetry={fetchTicket} />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/agent/tickets')}
            className="text-sm text-indigo-600 hover:text-indigo-500 mb-4"
          >
            ← Back to Tickets
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {ticket.reference} - {ticket.subject}
              </h1>
              <div className="mt-2 flex items-center space-x-4">
                <StatusBadge status={ticket.status} />
                <span className="text-sm text-gray-500">{ticket.category || 'General'}</span>
                <span className="text-sm text-gray-500">
                  Client ID: {ticket.client_id}
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              {ticket.status !== 'CLOSED' && (
                <>
                  {ticket.status !== 'ESCALATED' && (
                    <button
                      onClick={handleEscalate}
                      className="px-3 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50 text-sm"
                    >
                      Escalate
                    </button>
                  )}
                  <button
                    onClick={handleCloseTicket}
                    className="px-3 py-2 border border-green-300 text-green-700 rounded-md hover:bg-green-50 text-sm"
                  >
                    Close Ticket
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-3">Customer Description</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
          <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
            Created: {new Date(ticket.created_at).toLocaleString()}
            {ticket.updated_at !== ticket.created_at && (
              <> | Updated: {new Date(ticket.updated_at).toLocaleString()}</>
            )}
          </div>
        </div>

        {/* Responses */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Conversation History</h2>
          {ticket.responses.length === 0 ? (
            <p className="text-gray-500 italic">No responses yet</p>
          ) : (
            <div className="space-y-4">
              {ticket.responses.map((response) => (
                <div
                  key={response.id}
                  className={`p-4 rounded-lg ${
                    response.source === 'AI'
                      ? 'bg-blue-50 border border-blue-200'
                      : 'bg-green-50 border border-green-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-sm font-medium ${
                      response.source === 'AI' ? 'text-blue-700' : 'text-green-700'
                    }`}>
                      {response.source === 'AI' ? '🤖 AI Assistant' : '👤 Support Agent'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(response.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-700 whitespace-pre-wrap">{response.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reply Form - only if not closed */}
        {ticket.status !== 'CLOSED' && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Add Reply</h2>
            <form onSubmit={handleReply}>
              <textarea
                rows={4}
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Type your response to the customer..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
              <div className="mt-3 flex justify-end">
                <button
                  type="submit"
                  disabled={isSubmitting || !replyContent.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Sending...' : 'Send Reply'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Feedback Display */}
        {feedback.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Feedback</h3>
            {feedback.map((fb) => (
              <div key={fb.id} className="mb-4 last:mb-0">
                <div className="flex items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 mr-2">Rating:</span>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span
                      key={star}
                      className={`text-lg ${star <= fb.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                {fb.comment && (
                  <p className="text-gray-600 italic">"{fb.comment}"</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Submitted: {new Date(fb.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};
