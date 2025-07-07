import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import TrackingPage from './pages/TrackingPage';
import TripPlanningPage from './pages/TripPlanningPage';
import LogisticsDashboard from './pages/LogisticsDashboard';
import OrderProcessingPage from './pages/OrderProcessingPage';
import ManagementPage from './pages/ManagementPage';
import ManufacturerManagement from './pages/ManufacturerManagement';
import EmailManagement from './pages/EmailManagement';
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
                path="/upload"
                element={
                  <ProtectedRoute>
                    <UploadPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/tracking"
                element={
                  <ProtectedRoute>
                    <TrackingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/trip-planning"
                element={
                  <ProtectedRoute>
                    <TripPlanningPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/logistics"
                element={
                  <ProtectedRoute>
                    <LogisticsDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-processing"
                element={
                  <ProtectedRoute>
                    <OrderProcessingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-processing/:orderId"
                element={
                  <ProtectedRoute>
                    <OrderProcessingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/management"
                element={
                  <ProtectedRoute>
                    <ManagementPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/manufacturers"
                element={
                  <ProtectedRoute>
                    <ManufacturerManagement />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/emails"
                element={
                  <ProtectedRoute>
                    <EmailManagement />
                  </ProtectedRoute>
                }
              />
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
