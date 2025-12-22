import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { kbApi } from '../../api/kb';
import { KBDocument } from '../../types';
import { Layout } from '../../components/Layout';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';

export const KBDetailPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<KBDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!docId) return;
    setIsLoading(true);
    setError(null);
    try {
      const docData = await kbApi.getDocument(docId);
      setDocument(docData);
    } catch {
      setError('Failed to load document details');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [docId]);

  const handleDelete = async () => {
    if (!docId || !confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await kbApi.deleteDocument(docId);
      navigate('/admin/kb');
    } catch {
      alert('Failed to delete document');
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  if (error || !document) {
    return (
      <Layout>
        <ErrorMessage message={error || 'Document not found'} onRetry={fetchData} />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/admin/kb')}
            className="text-sm text-indigo-600 hover:text-indigo-500 mb-4"
          >
            ← Back to Knowledge Base
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{document.title}</h1>
              <div className="mt-2 flex items-center space-x-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {document.category || 'Uncategorized'}
                </span>
                <span className="text-sm text-gray-500">
                  Created: {new Date(document.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => navigate(`/admin/kb/${document.id}/edit`)}
                className="px-3 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 text-sm"
              >
                Edit Document
              </button>
              <button
                onClick={handleDelete}
                className="px-3 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 text-sm"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-3">Document Content</h2>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap text-gray-700 font-sans">{document.content}</pre>
          </div>
        </div>
      </div>
    </Layout>
  );
};
