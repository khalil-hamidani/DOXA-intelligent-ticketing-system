import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { metricsApi } from '../../api/metrics';
import { kbApi } from '../../api/kb';
import { MetricsOverview, KBDocument } from '../../types';
import { Layout } from '../../components/Layout';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import {
  LineChart,
  Line,
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

export const AdminDashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsOverview | null>(null);
  const [kbDocs, setKbDocs] = useState<KBDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [metricsData, kbData] = await Promise.all([
        metricsApi.getOverview(),
        kbApi.getDocuments(),
      ]);
      setMetrics(metricsData);
      setKbDocs(kbData);
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

  // Mock trend data (in a real app, this would come from the API)
  const trendData = [
    { day: 'Mon', tickets: 12, aiResolved: 8 },
    { day: 'Tue', tickets: 15, aiResolved: 11 },
    { day: 'Wed', tickets: 10, aiResolved: 7 },
    { day: 'Thu', tickets: 18, aiResolved: 14 },
    { day: 'Fri', tickets: 20, aiResolved: 16 },
    { day: 'Sat', tickets: 8, aiResolved: 6 },
    { day: 'Sun', tickets: 5, aiResolved: 4 },
  ];

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">System overview and knowledge base management</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Tickets</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{metrics.total_tickets}</dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">AI Resolution Rate</dt>
            <dd className="mt-1 text-3xl font-semibold text-green-600">
              {((metrics.ai_resolution_rate || 0) * 100).toFixed(1)}%
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Avg Response Time</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {(metrics.avg_response_time_minutes || 0).toFixed(0)}m
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Avg Satisfaction</dt>
            <dd className="mt-1 text-3xl font-semibold text-yellow-600">
              {(metrics.avg_satisfaction_rating || 0).toFixed(1)}/5
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">KB Documents</dt>
            <dd className="mt-1 text-3xl font-semibold text-indigo-600">{kbDocs.length}</dd>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Weekly Ticket Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="tickets" stroke="#4F46E5" strokeWidth={2} name="Total" />
              <Line type="monotone" dataKey="aiResolved" stroke="#10B981" strokeWidth={2} name="AI Resolved" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Ticket Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {statusData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* KB Documents Overview */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Knowledge Base</h3>
            <Link
              to="/admin/kb"
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              Manage KB →
            </Link>
          </div>
          <div className="p-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg mb-4">
              <div className="text-2xl font-bold text-gray-900">{kbDocs.length}</div>
              <div className="text-sm text-gray-500">Total Documents</div>
            </div>
            <Link
              to="/admin/kb/new"
              className="mt-4 w-full inline-flex justify-center items-center px-4 py-2 border border-indigo-300 text-indigo-700 rounded-md hover:bg-indigo-50"
            >
              + Add New Document
            </Link>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">System Health</h3>
          </div>
          <div className="p-6">
            <ul className="space-y-3">
              <li className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Status</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Operational
                </span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-sm text-gray-600">AI Service</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Connected
                </span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Healthy
                </span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Escalated Tickets</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  (metrics.tickets_by_status?.ESCALATED || 0) > 5
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {metrics.tickets_by_status?.ESCALATED || 0} pending
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
};
