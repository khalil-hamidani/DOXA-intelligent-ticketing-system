import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { metricsApi } from '../../api/metrics';
import { ticketsApi } from '../../api/tickets';
import { MetricsOverview, Ticket } from '../../types';
import { Layout } from '../../components/Layout';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#6B7280'];

export const AgentDashboardPage: React.FC = () => {
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

  const statusData = [
    { name: 'Open', value: metrics.tickets_by_status?.OPEN || 0 },
    { name: 'AI Answered', value: metrics.tickets_by_status?.AI_ANSWERED || 0 },
    { name: 'Escalated', value: metrics.tickets_by_status?.ESCALATED || 0 },
    { name: 'Closed', value: metrics.tickets_by_status?.CLOSED || 0 },
  ];

  const categoryData = Object.entries(metrics.tickets_by_category || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Agent Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Key metrics and recent escalated tickets</p>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Tickets</dt>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">AI Resolution Rate</dt>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Avg Response Time</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {(metrics.avg_response_time_minutes || 0).toFixed(0)} min
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Avg Satisfaction</dt>
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
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Tickets by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {statusData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Tickets by Category</h3>
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

      {/* Recent Escalated Tickets */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">Recent Escalated Tickets</h3>
          <Link
            to="/agent/tickets"
            className="text-sm text-indigo-600 hover:text-indigo-500"
          >
            View all →
          </Link>
        </div>
        <ul className="divide-y divide-gray-200">
          {recentTickets.length === 0 ? (
            <li className="px-6 py-4 text-gray-500 italic">No escalated tickets</li>
          ) : (
            recentTickets.map((ticket) => (
              <li key={ticket.id}>
                <Link to={`/agent/tickets/${ticket.id}`} className="block hover:bg-gray-50 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">{ticket.subject}</p>
                    <StatusBadge status={ticket.status} />
                  </div>
                  <div className="mt-2 flex justify-between text-sm text-gray-500">
                    <span>{ticket.category || 'General'}</span>
                    <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              </li>
            ))
          )}
        </ul>
      </div>
    </Layout>
  );
};
