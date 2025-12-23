import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { TicketDetail, Feedback } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { useLanguage } from '../../context/LanguageContext';

export const AgentTicketDetailPage: React.FC = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
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
      const fbData = await ticketsApi.getFeedback(ticketId);
      setFeedback(fbData);
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
            ← {t('common.backTo')} {t('nav.tickets')}
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {ticket.reference} - {ticket.subject}
              </h1>
              <div className="mt-2 flex items-center space-x-4">
                <StatusBadge status={ticket.status} />
                <span className="text-sm text-gray-500">{t(`categories.${ticket.category}`) || t('categories.general')}</span>
                <span className="text-sm text-gray-500">
                  {t('tickets.clientId')}: {ticket.client_id}
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
                      {t('tickets.escalate')}
                    </button>
                  )}
                  <button
                    onClick={handleCloseTicket}
                    className="px-3 py-2 border border-green-300 text-green-700 rounded-md hover:bg-green-50 text-sm"
                  >
                    {t('tickets.closeTicket')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-3">{t('tickets.customerDescription')}</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
          <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
            {t('tickets.created')}: {new Date(ticket.created_at).toLocaleString()}
            {ticket.updated_at !== ticket.created_at && (
              <> | {t('tickets.updated')}: {new Date(ticket.updated_at).toLocaleString()}</>
            )}
          </div>
        </div>

        {/* Attachments */}
        {ticket.attachments && ticket.attachments.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">{t('tickets.attachments')}</h2>
            <ul className="space-y-2">
              {ticket.attachments.map((attachment) => (
                <li key={attachment.id} className="flex items-center justify-between bg-gray-50 px-4 py-3 rounded-md border">
                  <div className="flex items-center space-x-3">
                    {attachment.file_type?.startsWith('image/') ? (
                      <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    ) : (
                      <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-700">{attachment.original_filename}</p>
                      <p className="text-xs text-gray-500">
                        {attachment.file_size ? `${(attachment.file_size / 1024).toFixed(1)} KB` : ''}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => ticketsApi.downloadAttachment(ticket.id, attachment.id, attachment.original_filename)}
                    className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center space-x-1"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>{t('common.download')}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Responses */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">{t('tickets.conversationHistory')}</h2>
          {ticket.responses.length === 0 ? (
            <p className="text-gray-500 italic">{t('tickets.noResponses')}</p>
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
                      {response.source === 'AI' ? `🤖 ${t('tickets.aiAssistant')}` : `👤 ${t('tickets.supportAgent')}`}
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
            <h2 className="text-lg font-medium text-gray-900 mb-4">{t('tickets.addReply')}</h2>
            <form onSubmit={handleReply}>
              <textarea
                rows={4}
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder={t('tickets.replyPlaceholder')}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
              <div className="mt-3 flex justify-end">
                <button
                  type="submit"
                  disabled={isSubmitting || !replyContent.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmitting ? t('tickets.sending') : t('tickets.sendReply')}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Feedback Display */}
        {feedback && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">{t('feedback.customerFeedback')}</h3>
            <div className="flex items-center mb-2">
              <span className="text-sm font-medium text-gray-700 mr-2">{t('feedback.satisfaction')}:</span>
              <span className={`text-lg font-semibold ${feedback.satisfied ? 'text-green-600' : 'text-red-600'}`}>
                {feedback.satisfied ? `👍 ${t('feedback.satisfied')}` : `👎 ${t('feedback.notSatisfied')}`}
              </span>
            </div>
            {feedback.comment && (
              <p className="text-gray-600 italic">"{feedback.comment}"</p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              {t('feedback.submittedOn')}: {new Date(feedback.created_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};
