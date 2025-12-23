import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage, Language } from '../context/LanguageContext';
import { USER_ROLES } from '../config/constants';

const LANGUAGE_LABELS: Record<Language, string> = {
  en: 'EN',
  fr: 'FR',
  ar: 'AR'
};

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const { t, isRTL, language, setLanguage } = useLanguage();
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
          { to: '/client/tickets', label: t('nav.myTickets') },
          { to: '/client/tickets/new', label: t('nav.createTicket') },
        ];
      case USER_ROLES.AGENT:
        return [
          { to: '/agent/dashboard', label: t('nav.dashboard') },
          { to: '/agent/kb', label: t('nav.knowledgeBase') },
        ];
      case USER_ROLES.ADMIN:
        return [
          { to: '/admin/dashboard', label: t('nav.dashboard') },
          { to: '/admin/users', label: t('nav.users') },
          { to: '/admin/kb', label: t('nav.knowledgeBase') },
          { to: '/admin/kb/new', label: t('nav.createKBArticle') },
        ];
      default:
        return [];
    }
  };

  return (
    <div className={`min-h-screen bg-gray-100 ${isRTL ? 'rtl' : 'ltr'}`} dir={isRTL ? 'rtl' : 'ltr'}>
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
              <div className={`hidden sm:flex sm:space-x-8 ${isRTL ? 'sm:mr-6' : 'sm:ml-6'}`}>
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
            <div className={`flex items-center ${isRTL ? 'space-x-reverse' : ''} space-x-4`}>
              {/* Quick Language Switcher */}
              <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden">
                {(['en', 'fr', 'ar'] as Language[]).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    className={`px-2 py-1 text-sm font-medium transition-colors ${
                      language === lang
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'bg-white hover:bg-gray-50 text-gray-600'
                    }`}
                    title={lang.toUpperCase()}
                  >
                    {LANGUAGE_LABELS[lang]}
                  </button>
                ))}
              </div>
              {user && (
                <>
                  <Link to="/profile" className={`flex items-center ${isRTL ? 'space-x-reverse' : ''} space-x-2 text-sm text-gray-600 hover:text-gray-900`}>
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
                    {t(`roles.${user.role}`)}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    {t('nav.logout')}
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
