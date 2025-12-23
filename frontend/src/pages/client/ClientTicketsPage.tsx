import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { Ticket } from '../../types';
import { Layout } from '../../components/Layout';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { EmptyState } from '../../components/EmptyState';
import { ErrorMessage } from '../../components/ErrorMessage';
import { TICKET_CATEGORIES } from '../../config/constants';
import { useLanguage } from '../../context/LanguageContext';

export const ClientTicketsPage: React.FC = () => {
  const { t } = useLanguage();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  const fetchTickets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await ticketsApi.getMyTickets({
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
      });
      setTickets(data);
    } catch {
      setError(t('common.error'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, categoryFilter]);

  return (
    <Layout>
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('tickets.title')}</h1>
          <p className="mt-1 text-sm text-gray-500">{t('tickets.subtitle')}</p>
        </div>
        <Link
          to="/client/tickets/new"
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          {t('tickets.newTicket')}
        </Link>
      </div>

      {/* Filters */}
      <div className="mt-6 flex flex-col sm:flex-row gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block w-full sm:w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="">{t('tickets.allStatuses')}</option>
          <option value="OPEN">{t('status.OPEN')}</option>
          <option value="AI_ANSWERED">{t('status.AI_ANSWERED')}</option>
          <option value="ESCALATED">{t('status.ESCALATED')}</option>
          <option value="CLOSED">{t('status.CLOSED')}</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="block w-full sm:w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="">{t('tickets.allCategories')}</option>
          {Object.keys(TICKET_CATEGORIES).map((key) => (
            <option key={key} value={key}>{t(`categories.${key}`)}</option>
          ))}
        </select>
      </div>

      {/* Content */}
      <div className="mt-6">
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchTickets} />
        ) : tickets.length === 0 ? (
          <EmptyState
            title={t('tickets.noTickets')}
            message={t('tickets.noTicketsMessage')}
            actionText={t('tickets.createTicket')}
            actionLink="/client/tickets/new"
          />
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {tickets.map((ticket) => (
                <li key={ticket.id}>
                  <Link to={`/client/tickets/${ticket.id}`} className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          {ticket.subject}
                        </p>
                        <div className="ml-2 flex-shrink-0">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            ticket.status === 'OPEN' ? 'bg-yellow-100 text-yellow-800' :
                            ticket.status === 'AI_ANSWERED' ? 'bg-blue-100 text-blue-800' :
                            ticket.status === 'ESCALATED' ? 'bg-red-100 text-red-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {t(`status.${ticket.status}`)}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {t(`categories.${ticket.category || 'GENERAL'}`)}
                            </span>
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>
                            {t('tickets.createdAt')}: {new Date(ticket.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
};
