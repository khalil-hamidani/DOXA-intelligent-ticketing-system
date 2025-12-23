import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketsApi } from '../../api/tickets';
import { Layout } from '../../components/Layout';
import { TICKET_CATEGORIES } from '../../config/constants';

const ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'application/pdf'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const CreateTicketPage: React.FC = () => {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const validFiles: File[] = [];
    const errors: string[] = [];

    selectedFiles.forEach(file => {
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        errors.push(`${file.name}: Invalid file type. Only images and PDFs are allowed.`);
      } else if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: File too large. Maximum size is 10MB.`);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setError(errors.join(' '));
    } else {
      setError('');
    }

    setFiles(prev => [...prev, ...validFiles]);
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      // Create ticket first
      const ticket = await ticketsApi.createTicket({ subject, description, category });
      
      // Upload attachments if any
      if (files.length > 0) {
        setUploadProgress('Uploading attachments...');
        for (let i = 0; i < files.length; i++) {
          setUploadProgress(`Uploading ${i + 1}/${files.length}: ${files[i].name}`);
          await ticketsApi.uploadAttachment(ticket.id, files[i]);
        }
      }
      
      navigate(`/client/tickets/${ticket.id}`);
    } catch {
      setError('Failed to create ticket. Please try again.');
    } finally {
      setIsSubmitting(false);
      setUploadProgress('');
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <div className="md:flex md:items-center md:justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Ticket</h1>
            <p className="mt-1 text-sm text-gray-500">
              Submit a support request and our AI will try to help you immediately
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow rounded-lg p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">
              Category *
            </label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
            >
              <option value="">Select a category</option>
              {Object.entries(TICKET_CATEGORIES).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700">
              Subject *
            </label>
            <input
              type="text"
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              maxLength={200}
              placeholder="Brief summary of your issue"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description *
            </label>
            <textarea
              id="description"
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="Please describe your issue in detail. Include any relevant information that might help us assist you."
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          {/* Attachment Upload Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attachments (optional)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".pdf,.png,.jpg,.jpeg,.gif"
                multiple
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <p className="mt-2 text-sm text-gray-600">
                  <span className="font-semibold text-indigo-600 hover:text-indigo-500">
                    Click to upload
                  </span>{' '}
                  or drag and drop
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  PNG, JPG, GIF or PDF up to 10MB
                </p>
              </label>
            </div>

            {/* File Preview List */}
            {files.length > 0 && (
              <ul className="mt-4 space-y-2">
                {files.map((file, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between bg-gray-50 px-4 py-2 rounded-md border"
                  >
                    <div className="flex items-center space-x-3">
                      {file.type.startsWith('image/') ? (
                        <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      ) : (
                        <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-700 truncate max-w-xs">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  <strong>AI-Powered Support:</strong> Our AI assistant will analyze your request and provide an immediate response. If the AI can't fully resolve your issue, your ticket will be escalated to a human agent.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate('/client/tickets')}
              disabled={isSubmitting}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? (uploadProgress || 'Submitting...') : 'Submit Ticket'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};
