import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import en from '../translations/en.json';
import fr from '../translations/fr.json';
import ar from '../translations/ar.json';

export type Language = 'en' | 'fr' | 'ar';
type Translations = typeof en;

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  isRTL: boolean;
}

const translations: Record<Language, Translations> = { en, fr, ar };

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Helper to get nested translation value
const getNestedValue = (obj: Record<string, unknown>, path: string): string => {
  const keys = path.split('.');
  let result: unknown = obj;
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = (result as Record<string, unknown>)[key];
    } else {
      return path; // Return key if not found
    }
  }
  
  return typeof result === 'string' ? result : path;
};

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initialize from localStorage or default to 'en'
  const [language, setLanguageState] = useState<Language>(() => {
    const stored = localStorage.getItem('app_language');
    if (stored && ['en', 'fr', 'ar'].includes(stored)) {
      return stored as Language;
    }
    return 'en';
  });

  const isRTL = language === 'ar';

  // Apply RTL direction to document
  useEffect(() => {
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
    
    // Add/remove RTL class for additional styling hooks
    if (isRTL) {
      document.body.classList.add('rtl');
    } else {
      document.body.classList.remove('rtl');
    }
  }, [language, isRTL]);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('app_language', lang);
  };

  // Translation function
  const t = (key: string): string => {
    return getNestedValue(translations[language] as unknown as Record<string, unknown>, key);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

// Sync language with user profile
export const useSyncLanguageWithUser = (userLanguage: string | undefined | null) => {
  const { setLanguage } = useLanguage();
  
  useEffect(() => {
    if (userLanguage && ['en', 'fr', 'ar'].includes(userLanguage)) {
      setLanguage(userLanguage as Language);
    }
  }, [userLanguage, setLanguage]);
};
