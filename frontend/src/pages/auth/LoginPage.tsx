import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { USER_ROLES } from '../../config/constants';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const { t, isRTL } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const { access_token } = await authApi.login(email, password);
      await login(access_token);
      
      // Redirect based on role
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      switch (user.role) {
        case USER_ROLES.CLIENT:
          navigate('/client/tickets');
          break;
        case USER_ROLES.AGENT:
          navigate('/agent/dashboard');
          break;
        case USER_ROLES.ADMIN:
          navigate('/admin/dashboard');
          break;
        default:
          navigate('/');
      }
    } catch {
      setError('Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex ${isRTL ? 'flex-row-reverse' : ''}`} dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/30 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/30 rounded-full filter blur-3xl"></div>
        </div>
        
        <div className="relative z-10 flex flex-col justify-center px-12 lg:px-16">
          <Link to="/" className="mb-8">
            <span className="text-4xl font-bold text-white">DOXA</span>
          </Link>
          <h1 className="text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
            {t('auth.welcomeBack')}
          </h1>
          <p className="text-xl text-indigo-100 mb-4">
            {t('landing.tagline')}
          </p>
          <p className="text-indigo-200 max-w-md">
            {t('landing.subtitle')}
          </p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-gray-100 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl p-8 sm:p-10">
            {/* Logo for mobile */}
            <div className="lg:hidden text-center mb-8">
              <Link to="/">
                <span className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  DOXA
                </span>
              </Link>
            </div>

            {/* Desktop Logo in form */}
            <div className="hidden lg:flex items-center justify-center mb-8">
              <div className={`flex items-center ${isRTL ? 'space-x-reverse' : ''} space-x-2`}>
                <div className="flex space-x-0.5">
                  <div className="w-1 h-8 bg-indigo-600 rounded-full"></div>
                  <div className="w-1 h-8 bg-indigo-500 rounded-full"></div>
                  <div className="w-1 h-8 bg-indigo-400 rounded-full"></div>
                </div>
                <span className="text-2xl font-bold text-indigo-900">Doxa</span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.email')}
                </label>
                <div className="relative">
                  <div className={`absolute inset-y-0 ${isRTL ? 'right-0 pr-3' : 'left-0 pl-3'} flex items-center pointer-events-none`}>
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    className={`block w-full ${isRTL ? 'pr-10 pl-10' : 'pl-10 pr-10'} py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all`}
                    placeholder="olivia@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.password')}
                </label>
                <div className="relative">
                  <div className={`absolute inset-y-0 ${isRTL ? 'right-0 pr-3' : 'left-0 pl-3'} flex items-center pointer-events-none`}>
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    className={`block w-full ${isRTL ? 'pr-10 pl-10' : 'pl-10 pr-10'} py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all`}
                    placeholder="••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              <div className={`${isRTL ? 'text-right' : 'text-left'}`}>
                <button type="button" className="text-sm text-indigo-600 hover:text-indigo-500">
                  {t('auth.forgotPassword')}
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent text-base font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-all shadow-lg shadow-indigo-200"
              >
                {isLoading ? t('common.loading') : t('auth.login')}
              </button>

              <div className="text-center pt-4">
                <span className="text-sm text-gray-600">{t('auth.noAccount')} </span>
                <Link to="/register" className="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
                  {t('auth.signUp')}
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
