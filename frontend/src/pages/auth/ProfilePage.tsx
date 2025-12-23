import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Layout } from '../../components/Layout';
import { authApi } from '../../api/auth';

const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' },
];

export const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { setLanguage: setAppLanguage, t } = useLanguage();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [language, setLanguage] = useState(user?.language || 'en');
  const [profilePictureUrl, setProfilePictureUrl] = useState(user?.profile_picture_url || '');

  // Sync app language with user profile on mount
  useEffect(() => {
    if (user?.language && ['en', 'fr', 'ar'].includes(user.language)) {
      setAppLanguage(user.language as 'en' | 'fr' | 'ar');
    }
  }, [user?.language, setAppLanguage]);

  if (!user) return null;

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    // Immediately apply language change to UI
    if (['en', 'fr', 'ar'].includes(newLang)) {
      setAppLanguage(newLang as 'en' | 'fr' | 'ar');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password && password !== confirmPassword) {
      setError(t('profile.passwordMismatch'));
      return;
    }

    setIsLoading(true);
    try {
      const updateData: { password?: string; language?: string; profile_picture_url?: string } = {};
      
      if (password) updateData.password = password;
      if (language !== user.language) updateData.language = language;
      if (profilePictureUrl !== (user.profile_picture_url || '')) {
        updateData.profile_picture_url = profilePictureUrl || undefined;
      }

      if (Object.keys(updateData).length === 0) {
        setError(t('profile.noChanges'));
        setIsLoading(false);
        return;
      }

      await authApi.updateProfile(updateData);
      
      // Refresh user data
      await refreshUser();
      
      setSuccess(t('profile.updateSuccess'));
      setPassword('');
      setConfirmPassword('');
      setIsEditing(false);
    } catch {
      setError(t('profile.updateError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setPassword('');
    setConfirmPassword('');
    setLanguage(user.language);
    // Revert language to user's saved preference
    if (user.language && ['en', 'fr', 'ar'].includes(user.language)) {
      setAppLanguage(user.language as 'en' | 'fr' | 'ar');
    }
    setProfilePictureUrl(user.profile_picture_url || '');
    setError(null);
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">{t('profile.title')}</h3>
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="inline-flex items-center px-3 py-2 border border-indigo-300 text-sm font-medium rounded-md text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  {t('profile.editProfile')}
                </button>
              )}
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                {success}
              </div>
            )}

            {/* Profile Picture Display */}
            <div className="flex items-center mb-6 pb-6 border-b border-gray-200">
              {user.profile_picture_url ? (
                <img 
                  src={user.profile_picture_url} 
                  alt="Profile" 
                  className="w-20 h-20 rounded-full object-cover border-4 border-indigo-200"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-indigo-100 flex items-center justify-center">
                  <svg className="w-10 h-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              )}
              <div className="ml-4">
                <p className="text-lg font-medium text-gray-900">{user.email}</p>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {user.role}
                </span>
              </div>
            </div>

            {isEditing ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Language Selector - Prominent Position */}
                <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                  <label className="block text-sm font-medium text-indigo-800 mb-3">
                    {t('profile.language')}
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <button
                        key={lang.code}
                        type="button"
                        onClick={() => handleLanguageChange(lang.code)}
                        className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${
                          language === lang.code
                            ? 'border-indigo-600 bg-white shadow-md'
                            : 'border-gray-200 bg-white hover:border-indigo-300'
                        }`}
                      >
                        <span className="text-2xl mb-1">{lang.flag}</span>
                        <span className={`text-sm font-medium ${
                          language === lang.code ? 'text-indigo-600' : 'text-gray-700'
                        }`}>
                          {lang.label}
                        </span>
                        {language === lang.code && (
                          <svg className="w-4 h-4 text-indigo-600 mt-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label htmlFor="profilePictureUrl" className="block text-sm font-medium text-gray-700">
                    {t('profile.profilePicture')}
                  </label>
                  <input
                    type="url"
                    id="profilePictureUrl"
                    value={profilePictureUrl}
                    onChange={(e) => setProfilePictureUrl(e.target.value)}
                    placeholder="https://example.com/your-image.jpg"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                </div>

                <div className="border-t border-gray-200 pt-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-4">{t('profile.newPassword')}</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                        {t('profile.newPassword')}
                      </label>
                      <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      />
                    </div>

                    <div>
                      <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                        {t('profile.confirmNewPassword')}
                      </label>
                      <input
                        type="password"
                        id="confirmPassword"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {isLoading ? t('common.loading') : t('common.save')}
                  </button>
                </div>
              </form>
            ) : (
              <dl className="divide-y divide-gray-200">
                <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">{t('auth.email')}</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">{user.email}</dd>
                </div>
                <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">{t('profile.role')}</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {user.role}
                    </span>
                  </dd>
                </div>
                <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">{t('profile.language')}</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
                    {(() => {
                      const lang = LANGUAGE_OPTIONS.find(l => l.code === user.language);
                      return lang ? `${lang.flag} ${lang.label}` : user.language;
                    })()}
                  </dd>
                </div>
                <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">{t('profile.status')}</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
                    {user.is_active ? (
                      <span className="text-green-600">{t('profile.active')}</span>
                    ) : (
                      <span className="text-red-600">{t('profile.inactive')}</span>
                    )}
                  </dd>
                </div>
              </dl>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
