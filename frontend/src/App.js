import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import OrderCreationPage from './pages/OrderCreationPage';
import FMCGOrderAggregationPage from './pages/FMCGOrderAggregationPage';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-creation"
                element={
                  <ProtectedRoute>
                    <OrderCreationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-aggregation"
                element={
                  <ProtectedRoute>
                    <FMCGOrderAggregationPage />
                  </ProtectedRoute>
                }
              />
              {/* Legacy routes redirected to new consolidated pages */}
              <Route path="/upload" element={<Navigate to="/order-creation" replace />} />
              <Route path="/tracking" element={<Navigate to="/order-creation" replace />} />
              <Route path="/order-processing" element={<Navigate to="/order-creation" replace />} />
              <Route path="/order-processing/:orderId" element={<Navigate to="/order-creation" replace />} />
              <Route path="/trip-planning" element={<Navigate to="/order-aggregation" replace />} />
              <Route path="/logistics" element={<Navigate to="/order-aggregation" replace />} />
              <Route path="/management" element={<Navigate to="/order-aggregation" replace />} />
              <Route path="/manufacturers" element={<Navigate to="/order-aggregation" replace />} />
              <Route path="/emails" element={<Navigate to="/order-aggregation" replace />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
