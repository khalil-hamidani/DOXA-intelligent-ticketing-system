import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { Ticket } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { EmptyState } from '../../components/EmptyState';
import { ErrorMessage } from '../../components/ErrorMessage';
import { TICKET_CATEGORIES } from '../../config/constants';

export const AgentTicketsPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ESCALATED');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchTickets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await ticketsApi.getAllTickets({
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        search: searchQuery || undefined,
      });
      setTickets(data);
    } catch {
      setError('Failed to load tickets');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, categoryFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTickets();
  };

  return (
    <Layout>
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">All Tickets</h1>
          <p className="mt-1 text-sm text-gray-500">Manage and respond to customer tickets</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mt-6 space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by reference or subject..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm font-medium"
          >
            Search
          </button>
        </form>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="block w-full sm:w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="AI_ANSWERED">AI Answered</option>
            <option value="ESCALATED">Escalated (Priority)</option>
            <option value="CLOSED">Closed</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="block w-full sm:w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
          >
            <option value="">All Categories</option>
            {Object.entries(TICKET_CATEGORIES).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <button
            onClick={fetchTickets}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 flex gap-4 text-sm text-gray-500">
        <span>{tickets.length} tickets found</span>
        {statusFilter === 'ESCALATED' && (
          <span className="text-orange-600 font-medium">
            ⚠️ Showing escalated tickets requiring attention
          </span>
        )}
      </div>

      {/* Content */}
      <div className="mt-6">
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchTickets} />
        ) : tickets.length === 0 ? (
          <EmptyState
            title="No tickets found"
            message={statusFilter === 'ESCALATED' 
              ? "Great job! No escalated tickets at the moment."
              : "No tickets match the current filters."
            }
          />
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {tickets.map((ticket) => (
                <li key={ticket.id}>
                  <Link to={`/agent/tickets/${ticket.id}`} className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <p className="text-sm font-medium text-indigo-600 truncate">
                            {ticket.reference} - {ticket.subject}
                          </p>
                          {ticket.status === 'ESCALATED' && (
                            <span className="ml-2 text-orange-500">🔥</span>
                          )}
                        </div>
                        <div className="ml-2 flex-shrink-0">
                          <StatusBadge status={ticket.status} />
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex space-x-4">
                          <p className="flex items-center text-sm text-gray-500">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {ticket.category || 'General'}
                            </span>
                          </p>
                          <p className="text-sm text-gray-500">
                            Client ID: {ticket.client_id}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>
                            {new Date(ticket.created_at).toLocaleString()}
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
