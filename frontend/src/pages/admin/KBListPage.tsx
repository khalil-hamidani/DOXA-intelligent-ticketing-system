import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { kbApi } from '../../api/kb';
import { KBDocument } from '../../types';
import { Layout } from '../../components/Layout';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { EmptyState } from '../../components/EmptyState';
import { ErrorMessage } from '../../components/ErrorMessage';

export const KBListPage: React.FC = () => {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await kbApi.getDocuments(categoryFilter || undefined);
      setDocuments(data);
    } catch {
      setError('Failed to load knowledge base documents');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [categoryFilter]);

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await kbApi.deleteDocument(docId);
      fetchDocuments();
    } catch {
      alert('Failed to delete document');
    }
  };

  // Get unique categories (filter out nulls)
  const categories = [...new Set(documents.map(d => d.category).filter((c): c is string => c !== null))];

  return (
    <Layout>
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage documents that power AI responses
          </p>
        </div>
        <Link
          to="/admin/kb/new"
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          + Add Document
        </Link>
      </div>

      {/* Filter */}
      <div className="mt-6">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="block w-full sm:w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
        >
          <option value="">All Categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>

      {/* Content */}
      <div className="mt-6">
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchDocuments} />
        ) : documents.length === 0 ? (
          <EmptyState
            title="No documents found"
            message="Add knowledge base documents to help the AI answer customer questions"
            actionText="Add Document"
            actionLink="/admin/kb/new"
          />
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <li key={doc.id}>
                  <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <Link 
                        to={`/admin/kb/${doc.id}`}
                        className="text-sm font-medium text-indigo-600 truncate hover:underline"
                      >
                        {doc.title}
                      </Link>
                      <div className="ml-2 flex-shrink-0 flex space-x-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {doc.category || 'Uncategorized'}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="text-sm text-gray-500 line-clamp-2">
                          {doc.content.substring(0, 150)}...
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 flex justify-between items-center">
                      <div className="text-xs text-gray-500">
                        Created: {new Date(doc.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex space-x-2">
                        <Link
                          to={`/admin/kb/${doc.id}/edit`}
                          className="text-sm text-gray-600 hover:text-gray-800"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
};
