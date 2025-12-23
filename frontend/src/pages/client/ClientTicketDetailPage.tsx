import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { TicketDetail, Feedback } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { useLanguage } from '../../context/LanguageContext';

export const ClientTicketDetailPage: React.FC = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(0);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  const fetchTicket = async () => {
    if (!ticketId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await ticketsApi.getTicket(ticketId);
      setTicket(data);
      // Check if feedback already exists
      const fbData = await ticketsApi.getFeedback(ticketId);
      if (fbData) {
        setFeedback(fbData);
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
      const submittedFeedback = await ticketsApi.submitFeedback(ticketId, {
        satisfied: feedbackRating >= 3,
        comment: feedbackComment || undefined,
      });
      setFeedback(submittedFeedback);
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
            ← {t('common.backTo')} {t('nav.tickets')}
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{ticket.subject}</h1>
              <div className="mt-2 flex items-center space-x-4">
                <StatusBadge status={ticket.status} />
                <span className="text-sm text-gray-500">{t(`categories.${ticket.category}`) || t('categories.general')}</span>
                <span className="text-sm text-gray-500">
                  {t('tickets.created')} {new Date(ticket.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-3">{t('tickets.description')}</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
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
          <h2 className="text-lg font-medium text-gray-900 mb-4">{t('tickets.responses')}</h2>
          {ticket.responses.length === 0 ? (
            <p className="text-gray-500 italic">{t('common.waitingForResponse')}</p>
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

        {/* Actions for AI_ANSWERED status */}
        {ticket.status === 'AI_ANSWERED' && latestAiResponse && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-yellow-800 mb-2">{t('tickets.wasResponseHelpful')}</h3>
            <p className="text-sm text-yellow-700 mb-4">
              {t('tickets.aiResponseNotHelpful')}
            </p>
            <button
              onClick={handleRequestEscalation}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
            >
              {t('tickets.escalateToAgent')}
            </button>
          </div>
        )}

        {/* Feedback Form - only show if ticket is closed AND no feedback exists yet */}
        {ticket.status === 'CLOSED' && !feedback && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-green-800 mb-4">{t('feedback.rateExperience')}</h3>
            <form onSubmit={handleSubmitFeedback}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-green-700 mb-2">
                  {t('feedback.howWouldYouRate')}
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
                  {t('feedback.additionalComments')}
                </label>
                <textarea
                  rows={3}
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  className="w-full border border-green-300 rounded-md px-3 py-2"
                  placeholder={t('feedback.commentPlaceholder')}
                />
              </div>
              <button
                type="submit"
                disabled={feedbackRating === 0 || isSubmittingFeedback}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {isSubmittingFeedback ? t('common.submitting') : t('feedback.submitFeedback')}
              </button>
            </form>
          </div>
        )}

        {/* Feedback Display - show when feedback exists */}
        {feedback && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('feedback.yourFeedback')}</h3>
            <div className="flex items-center mb-2">
              <span className={`text-lg font-medium ${feedback.satisfied ? 'text-green-600' : 'text-red-600'}`}>
                {feedback.satisfied ? `👍 ${t('feedback.satisfied')}` : `👎 ${t('feedback.notSatisfied')}`}
              </span>
            </div>
            {feedback.comment && <p className="text-gray-600 italic">"{feedback.comment}"</p>}
            <p className="text-xs text-gray-500 mt-2">
              {t('feedback.submittedOn')} {new Date(feedback.created_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};
