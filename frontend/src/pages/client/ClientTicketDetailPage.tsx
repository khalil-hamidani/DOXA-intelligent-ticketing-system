import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { TicketDetail, Feedback } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';

export const ClientTicketDetailPage: React.FC = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(0);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const fetchTicket = async () => {
    if (!ticketId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await ticketsApi.getTicket(ticketId);
      setTicket(data);
      // Check if feedback already exists
      try {
        const fbData = await ticketsApi.getFeedback(ticketId);
        if (fbData && fbData.length > 0) {
          setFeedback(fbData);
          setFeedbackSubmitted(true);
        }
      } catch {
        // No feedback yet, that's ok
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

  const handleRequestEscalation = async () => {
    if (!ticketId) return;
    try {
      await ticketsApi.escalateTicket(ticketId);
      fetchTicket();
    } catch {
      alert('Failed to escalate ticket');
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketId || feedbackRating === 0) return;
    
    setIsSubmittingFeedback(true);
    try {
      await ticketsApi.submitFeedback(ticketId, {
        rating: feedbackRating,
        comment: feedbackComment || undefined,
      });
      setFeedbackSubmitted(true);
      fetchTicket();
    } catch {
      alert('Failed to submit feedback');
    } finally {
      setIsSubmittingFeedback(false);
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

  const latestAiResponse = ticket.responses.find(r => r.source === 'AI');

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/client/tickets')}
            className="text-sm text-indigo-600 hover:text-indigo-500 mb-4"
          >
            ← Back to Tickets
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{ticket.subject}</h1>
              <div className="mt-2 flex items-center space-x-4">
                <StatusBadge status={ticket.status} />
                <span className="text-sm text-gray-500">{ticket.category || 'General'}</span>
                <span className="text-sm text-gray-500">
                  Created {new Date(ticket.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-3">Description</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
        </div>

        {/* Responses */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Responses</h2>
          {ticket.responses.length === 0 ? (
            <p className="text-gray-500 italic">Waiting for response...</p>
          ) : (
            <div className="space-y-4">
              {ticket.responses.map((response) => (
                <div
                  key={response.id}
                  className={`p-4 rounded-lg ${
                    response.source === 'AI'
                      ? 'bg-blue-50 border border-blue-200'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-sm font-medium ${
                      response.source === 'AI' ? 'text-blue-700' : 'text-gray-700'
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

        {/* Actions for AI_ANSWERED status */}
        {ticket.status === 'AI_ANSWERED' && latestAiResponse && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-yellow-800 mb-2">Was this response helpful?</h3>
            <p className="text-sm text-yellow-700 mb-4">
              If the AI response didn't resolve your issue, you can request escalation to a human agent.
            </p>
            <button
              onClick={handleRequestEscalation}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
            >
              Escalate to Human Agent
            </button>
          </div>
        )}

        {/* Feedback Form */}
        {ticket.status === 'CLOSED' && !feedbackSubmitted && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-green-800 mb-4">Rate Your Experience</h3>
            <form onSubmit={handleSubmitFeedback}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-green-700 mb-2">
                  How would you rate the support you received?
                </label>
                <div className="flex space-x-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      onClick={() => setFeedbackRating(rating)}
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
                        feedbackRating >= rating
                          ? 'bg-yellow-400 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-green-700 mb-2">
                  Additional comments (optional)
                </label>
                <textarea
                  rows={3}
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  className="w-full border border-green-300 rounded-md px-3 py-2"
                  placeholder="Tell us more about your experience..."
                />
              </div>
              <button
                type="submit"
                disabled={feedbackRating === 0 || isSubmittingFeedback}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </form>
          </div>
        )}

        {/* Feedback Display */}
        {feedbackSubmitted && feedback.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Your Feedback</h3>
            {feedback.map((fb: Feedback) => (
              <div key={fb.id}>
                <div className="flex items-center mb-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span
                      key={star}
                      className={`text-lg ${star <= fb.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                {fb.comment && <p className="text-gray-600">{fb.comment}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};
