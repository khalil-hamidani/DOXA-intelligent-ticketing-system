import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { metricsApi } from '../../api/metrics';
import { ticketsApi } from '../../api/tickets';
import { MetricsOverview, Ticket } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { useLanguage } from '../../context/LanguageContext';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export const AgentDashboardPage: React.FC = () => {
  const { t } = useLanguage();
  const [metrics, setMetrics] = useState<MetricsOverview | null>(null);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [metricsData, ticketsData] = await Promise.all([
        metricsApi.getOverview(),
        ticketsApi.getAllTickets({ status: 'ESCALATED', limit: 5 }),
      ]);
      setMetrics(metricsData);
      setRecentTickets(ticketsData);
    } catch {
      setError('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  if (error || !metrics) {
    return (
      <Layout>
        <ErrorMessage message={error || 'Failed to load metrics'} onRetry={fetchData} />
      </Layout>
    );
  }

  const categoryData = Object.entries(metrics.tickets_by_category || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.agentDashboard')}</h1>
        <p className="mt-1 text-sm text-gray-500">{t('dashboard.subtitle')}</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm">📋</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">{t('dashboard.totalTickets')}</dt>
                  <dd className="text-lg font-semibold text-gray-900">{metrics.total_tickets}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm">🤖</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">{t('dashboard.aiResolutionRate')}</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {((metrics.ai_resolution_rate || 0) * 100).toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm">⏱</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">{t('dashboard.avgResponseTime')}</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {(metrics.avg_response_time_minutes || 0).toFixed(0)} {t('common.min')}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm">⭐</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">{t('dashboard.avgSatisfaction')}</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {(metrics.avg_satisfaction_rating || 0).toFixed(1)} / 5
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Recent Escalated Tickets - moved here */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">{t('dashboard.recentEscalated')}</h3>
            <Link
              to="/agent/tickets"
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              {t('dashboard.viewAllTickets')} →
            </Link>
          </div>
          <ul className="divide-y divide-gray-200">
            {recentTickets.length === 0 ? (
              <li className="px-6 py-4 text-gray-500 italic">{t('dashboard.noEscalatedTickets')}</li>
            ) : (
              recentTickets.map((ticket) => (
                <li key={ticket.id}>
                  <Link to={`/agent/tickets/${ticket.id}`} className="block hover:bg-gray-50 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-indigo-600 truncate">{ticket.reference} - {ticket.subject}</p>
                      <StatusBadge status={ticket.status} />
                    </div>
                    <div className="mt-2 flex justify-between text-sm text-gray-500">
                      <span>{t(`categories.${ticket.category}`) || t('categories.general')}</span>
                      <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                    </div>
                  </Link>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">{t('dashboard.ticketsByCategory')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#4F46E5" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Layout>
  );
};
