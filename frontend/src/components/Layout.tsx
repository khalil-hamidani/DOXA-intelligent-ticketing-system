import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { USER_ROLES } from '../config/constants';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getNavLinks = () => {
    if (!user) return [];
    
    switch (user.role) {
      case USER_ROLES.CLIENT:
        return [
          { to: '/client/tickets', label: 'My Tickets' },
          { to: '/client/tickets/new', label: 'Create Ticket' },
        ];
      case USER_ROLES.AGENT:
        return [
          { to: '/agent/dashboard', label: 'Dashboard' },
          { to: '/agent/kb', label: 'Knowledge Base' },
        ];
      case USER_ROLES.ADMIN:
        return [
          { to: '/admin/dashboard', label: 'Dashboard' },
          { to: '/admin/kb', label: 'Knowledge Base' },
          { to: '/admin/kb/new', label: 'Create KB Article' },
        ];
      default:
        return [];
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link to="/" className="flex items-center space-x-2">
                  <div className="flex space-x-0.5">
                    <div className="w-1 h-6 bg-indigo-600 rounded-full"></div>
                    <div className="w-1 h-6 bg-indigo-500 rounded-full"></div>
                    <div className="w-1 h-6 bg-indigo-400 rounded-full"></div>
                  </div>
                  <span className="text-xl font-bold text-indigo-900">Doxa</span>
                </Link>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {getNavLinks().map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {user && (
                <>
                  <Link to="/profile" className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900">
                    {user.profile_picture_url ? (
                      <img 
                        src={user.profile_picture_url} 
                        alt="Profile" 
                        className="w-8 h-8 rounded-full object-cover border-2 border-indigo-200"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                        <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                    )}
                    <span className="hidden md:inline">{user.email}</span>
                  </Link>
                  <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">
                    {user.role}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Logout
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
};
