import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { ThemeProvider } from './hooks/useTheme';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Onboarding } from './pages/Onboarding';
import { Stats } from './pages/Stats';
import { Preferences } from './pages/Preferences';
import { History } from './pages/History';
import { Scheduler } from './pages/Scheduler';
import { ArticleDetail } from './pages/ArticleDetail';
import { Trends } from './pages/Trends';
import { VoiceCompanion } from './pages/VoiceCompanion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { NotFound } from './pages/NotFound';
import { Profile } from './pages/Profile';
import { ForgotPassword } from './pages/ForgotPassword';
import { ResetPassword } from './pages/ResetPassword';
import { OAuthCallback } from './pages/OAuthCallback';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (!user?.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }
  
  return <>{children}</>;
}

function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }
  
  if (isAuthenticated) {
    if (!user?.onboarding_completed) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={
        <PublicOnlyRoute>
          <Login />
        </PublicOnlyRoute>
      } />
      <Route path="/register" element={
        <PublicOnlyRoute>
          <Register />
        </PublicOnlyRoute>
      } />
      <Route path="/forgot-password" element={
        <PublicOnlyRoute>
          <ForgotPassword />
        </PublicOnlyRoute>
      } />
      <Route path="/reset-password" element={
        <PublicOnlyRoute>
          <ResetPassword />
        </PublicOnlyRoute>
      } />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/articles/:id" element={<ArticleDetail />} />
                <Route path="/trends" element={<Trends />} />
                <Route path="/voice" element={<VoiceCompanion />} />
                <Route path="/stats" element={<Stats />} />
                <Route path="/preferences" element={<Preferences />} />
                <Route path="/history" element={<History />} />
                <Route path="/scheduler" element={<Scheduler />} />
                <Route path="/profile" element={<Profile />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ToastProvider>
            <BrowserRouter>
              <AuthProvider>
                <AppRoutes />
              </AuthProvider>
            </BrowserRouter>
          </ToastProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
