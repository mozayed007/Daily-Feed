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
import { useUser } from './hooks/useUser';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';

// Protected route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading } = useUser();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }
  
  // For PoC: redirect to onboarding if not completed
  // In production, check auth token
  if (!user?.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ToastProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/onboarding" element={<Onboarding />} />
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Routes>
                          <Route path="/" element={<Home />} />
                          <Route path="/stats" element={<Stats />} />
                          <Route path="/preferences" element={<Preferences />} />
                          <Route path="/history" element={<History />} />
                        </Routes>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </BrowserRouter>
          </ToastProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
