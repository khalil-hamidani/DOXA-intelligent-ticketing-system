import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { USER_ROLES } from './config/constants';

// Public pages
import { LandingPage } from './pages/public/LandingPage';

// Auth pages
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ProfilePage } from './pages/auth/ProfilePage';

// Client pages
import { ClientTicketsPage } from './pages/client/ClientTicketsPage';
import { CreateTicketPage } from './pages/client/CreateTicketPage';
import { ClientTicketDetailPage } from './pages/client/ClientTicketDetailPage';

// Agent pages
import { AgentDashboardPage } from './pages/agent/AgentDashboardPage';
import { AgentTicketsPage } from './pages/agent/AgentTicketsPage';
import { AgentTicketDetailPage } from './pages/agent/AgentTicketDetailPage';

// Admin pages
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { KBListPage } from './pages/admin/KBListPage';
import { KBCreatePage } from './pages/admin/KBCreatePage';
import { KBDetailPage } from './pages/admin/KBDetailPage';
import { KBEditPage } from './pages/admin/KBEditPage';

// Home redirect based on role
const HomeRedirect: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // If not logged in, show the landing page
  if (!user) {
    return <LandingPage />;
  }

  // If logged in, redirect to appropriate dashboard
  switch (user.role) {
    case USER_ROLES.CLIENT:
      return <Navigate to="/client/tickets" replace />;
    case USER_ROLES.AGENT:
      return <Navigate to="/agent/dashboard" replace />;
    case USER_ROLES.ADMIN:
      return <Navigate to="/admin/dashboard" replace />;
    default:
      return <Navigate to="/login" replace />;
  }
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Home redirect */}
      <Route path="/" element={<HomeRedirect />} />

      {/* Protected: Profile (all authenticated users) */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />

      {/* Client Routes */}
      <Route
        path="/client/tickets"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.CLIENT]}>
            <ClientTicketsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/tickets/new"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.CLIENT]}>
            <CreateTicketPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/tickets/:ticketId"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.CLIENT]}>
            <ClientTicketDetailPage />
          </ProtectedRoute>
        }
      />

      {/* Agent Routes */}
      <Route
        path="/agent/dashboard"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.AGENT, USER_ROLES.ADMIN]}>
            <AgentDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/tickets"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.AGENT, USER_ROLES.ADMIN]}>
            <AgentTicketsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/tickets/:ticketId"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.AGENT, USER_ROLES.ADMIN]}>
            <AgentTicketDetailPage />
          </ProtectedRoute>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <AdminDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/kb"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <KBListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/kb/new"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <KBCreatePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/kb/:docId"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <KBDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/kb/:docId/edit"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <KBEditPage />
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
