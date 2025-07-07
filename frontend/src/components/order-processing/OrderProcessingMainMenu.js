import React, { useState, useEffect, useCallback } from 'react';
import {
  Layout,
  CheckCircle,
  Mail,
  User,
  Settings,
  TrendingUp,
  Clock,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
  Bell,
  Download,
  Upload,
  Play,
  Pause
} from 'lucide-react';
import { getApiUrl } from '../../utils/apiConfig';

// Import the menu components
import OrderProcessingMenu from './OrderProcessingMenu';
import EmailCommunicationsManager from './EmailCommunicationsManager';
import UserActionsManager from './UserActionsManager';
import OrderProcessingDashboard from './OrderProcessingDashboard';

const OrderProcessingMainMenu = ({ orderId, onClose }) => {
  const [activeView, setActiveView] = useState('dashboard');
  const [orderStatus, setOrderStatus] = useState(null);
  const [processingMetrics, setProcessingMetrics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadOrderOverview = useCallback(async () => {
    setIsLoading(true);
    try {
      const [statusResponse, metricsResponse, notificationsResponse] = await Promise.all([
        fetch(getApiUrl(`api/orders/${orderId}/status`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(getApiUrl(`api/orders/${orderId}/processing-metrics`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(getApiUrl(`api/orders/${orderId}/notifications`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setOrderStatus(statusData.data);
      }

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setProcessingMetrics(metricsData.data);
      }

      if (notificationsResponse.ok) {
        const notificationsData = await notificationsResponse.json();
        setNotifications(notificationsData.data || []);
      }
    } catch (error) {
      console.error('Error loading order overview:', error);
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      loadOrderOverview();
    }
  }, [orderId, loadOrderOverview]);

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Layout,
      description: 'Overview of order processing status',
      component: OrderProcessingDashboard,
      count: null
    },
    {
      id: 'processing',
      label: 'Processing Steps',
      icon: Settings,
      description: 'Manage and monitor processing steps',
      component: OrderProcessingMenu,
      count: processingMetrics?.active_steps || 0
    },
    {
      id: 'communications',
      label: 'Email Communications',
      icon: Mail,
      description: 'Handle email communications',
      component: EmailCommunicationsManager,
      count: processingMetrics?.pending_emails || 0
    },
    {
      id: 'user_actions',
      label: 'User Actions',
      icon: User,
      description: 'Complete required user actions',
      component: UserActionsManager,
      count: processingMetrics?.pending_user_actions || 0
    },
    {
      id: 'validation',
      label: 'Validation Results',
      icon: CheckCircle,
      description: 'Review validation results and errors',
      component: null, // Will be handled by dashboard
      count: processingMetrics?.validation_errors || 0
    },
    {
      id: 'monitoring',
      label: 'System Monitoring',
      icon: TrendingUp,
      description: 'Monitor system performance and health',
      component: null, // Future implementation
      count: null
    }
  ];

  const renderActiveView = () => {
    const activeMenuItem = menuItems.find(item => item.id === activeView);
    if (!activeMenuItem || !activeMenuItem.component) {
      return <OrderProcessingDashboard orderId={orderId} />;
    }

    const Component = activeMenuItem.component;
    return <Component orderId={orderId} onClose={() => setActiveView('dashboard')} />;
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'processing': 'bg-blue-100 text-blue-800 border-blue-200',
      'completed': 'bg-green-100 text-green-800 border-green-200',
      'failed': 'bg-red-100 text-red-800 border-red-200',
      'paused': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[status] || colors.pending;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const handleQuickAction = async (action) => {
    try {
      const endpoint = getApiUrl(`api/orders/${orderId}/${action}`);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        await loadOrderOverview();
      }
    } catch (error) {
      console.error(`Error executing quick action ${action}:`, error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading order processing interface...</p>
        </div>
      </div>
    );
  }

  // Show the active view component if it's not the main menu
  if (activeView !== 'dashboard' && activeView !== 'main') {
    return renderActiveView();
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Order Processing Control Center</h1>
              <div className="flex items-center space-x-4 mt-2">
                <p className="text-sm text-gray-600">Order ID: {orderId}</p>
                {orderStatus && (
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(orderStatus.status)}
                    <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(orderStatus.status)}`}>
                      {orderStatus.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {notifications.length > 0 && (
                <div className="relative">
                  <Bell className="w-5 h-5 text-gray-600" />
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {notifications.length}
                  </span>
                </div>
              )}
              <button
                onClick={loadOrderOverview}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Order Status Overview */}
      {orderStatus && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Order Status Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-600">Processing Progress</p>
                    <p className="text-2xl font-bold text-blue-900">{orderStatus.progress || 0}%</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-blue-500" />
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-600">Completed Steps</p>
                    <p className="text-2xl font-bold text-green-900">{orderStatus.completed_steps || 0}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-yellow-600">Pending Actions</p>
                    <p className="text-2xl font-bold text-yellow-900">{orderStatus.pending_actions || 0}</p>
                  </div>
                  <Clock className="w-8 h-8 text-yellow-500" />
                </div>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-red-600">Issues</p>
                    <p className="text-2xl font-bold text-red-900">{orderStatus.issues || 0}</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <button
              onClick={() => handleQuickAction('restart-processing')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Play className="w-6 h-6 text-green-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Restart Processing</span>
            </button>
            <button
              onClick={() => handleQuickAction('pause-processing')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Pause className="w-6 h-6 text-yellow-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Pause Processing</span>
            </button>
            <button
              onClick={() => handleQuickAction('export-data')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Download className="w-6 h-6 text-blue-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Export Data</span>
            </button>
            <button
              onClick={() => handleQuickAction('import-corrections')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Upload className="w-6 h-6 text-purple-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Import Corrections</span>
            </button>
            <button
              onClick={() => setActiveView('user_actions')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <User className="w-6 h-6 text-orange-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">User Actions</span>
            </button>
            <button
              onClick={() => setActiveView('communications')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Mail className="w-6 h-6 text-indigo-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Send Email</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Menu Options */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium text-gray-900">Processing Management</h3>
            <p className="text-sm text-gray-600 mt-1">Select a section to manage order processing</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className="flex items-center p-6 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors text-left"
                >
                  <div className="flex-shrink-0">
                    <item.icon className="w-8 h-8 text-gray-600" />
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium text-gray-900">{item.label}</h4>
                      {item.count !== null && item.count > 0 && (
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                          {item.count}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                  </div>
                  <div className="flex-shrink-0 ml-4">
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      {notifications.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {notifications.slice(0, 5).map((notification, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      {getStatusIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                      <p className="text-sm text-gray-600">{notification.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(notification.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderProcessingMainMenu;
