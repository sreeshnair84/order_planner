import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileText, 
  CheckCircle, 
  Mail, 
  AlertTriangle, 
  Settings, 
  Play, 
  Pause, 
  RotateCcw,
  Eye,
  Edit,
  Send,
  RefreshCw,
  Clock,
  User,
  Database,
  Shield,
  ChevronRight,
  ChevronDown,
  Filter,
  Search
} from 'lucide-react';

const OrderProcessingMenu = ({ orderId, onClose }) => {
  const [processingSteps, setProcessingSteps] = useState([]);
  const [expandedSections, setExpandedSections] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  const loadProcessingSteps = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/requestedorders/${orderId}/processing-steps`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProcessingSteps(data.data || []);
      }
    } catch (error) {
      console.error('Error loading processing steps:', error);
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      loadProcessingSteps();
    }
  }, [orderId, loadProcessingSteps]);

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const executeAction = async (action, stepId, params = {}) => {
    try {
      const endpoint = getActionEndpoint(action, stepId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ orderId, stepId, ...params })
      });

      if (response.ok) {
        await loadProcessingSteps();
        return await response.json();
      } else {
        throw new Error(`Action failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error executing ${action}:`, error);
      throw error;
    }
  };

  const getActionEndpoint = (action, stepId) => {
    const endpoints = {
      'restart': `/api/requestedorders/${orderId}/restart-step`,
      'retry': `/api/requestedorders/${orderId}/retry-step`,
      'skip': `/api/requestedorders/${orderId}/skip-step`,
      'pause': `/api/requestedorders/${orderId}/pause-step`,
      'resume': `/api/requestedorders/${orderId}/resume-step`,
      'view_details': `/api/requestedorders/${orderId}/step-details`,
      'edit_params': `/api/requestedorders/${orderId}/edit-step-params`,
      'generate_email': `/api/requestedorders/${orderId}/generate-email`,
      'send_email': `/api/requestedorders/${orderId}/send-email`,
      'view_logs': `/api/requestedorders/${orderId}/step-logs`,
      'export_data': `/api/requestedorders/${orderId}/export-step-data`
    };
    return endpoints[action] || `/api/requestedorders/${orderId}/generic-action`;
  };

  const getStepIcon = (stepType) => {
    const icons = {
      'file_parsing': FileText,
      'validation': CheckCircle,
      'email_generation': Mail,
      'sku_processing': Database,
      'quality_check': Shield,
      'user_interaction': User,
      'system_process': Settings,
      'communication': Send,
      'error_handling': AlertTriangle
    };
    const IconComponent = icons[stepType] || Settings;
    return <IconComponent className="w-5 h-5" />;
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'text-gray-500 bg-gray-100',
      'running': 'text-blue-500 bg-blue-100',
      'completed': 'text-green-500 bg-green-100',
      'failed': 'text-red-500 bg-red-100',
      'paused': 'text-yellow-500 bg-yellow-100',
      'skipped': 'text-purple-500 bg-purple-100',
      'waiting_user': 'text-orange-500 bg-orange-100'
    };
    return colors[status] || colors.pending;
  };

  const processingSections = [
    {
      id: 'file_processing',
      title: 'File Processing',
      icon: FileText,
      steps: processingSteps.filter(step => step.category === 'file_processing')
    },
    {
      id: 'validation',
      title: 'Order Validation',
      icon: CheckCircle,
      steps: processingSteps.filter(step => step.category === 'validation')
    },
    {
      id: 'communication',
      title: 'Email Communications',
      icon: Mail,
      steps: processingSteps.filter(step => step.category === 'communication')
    },
    {
      id: 'sku_processing',
      title: 'SKU Processing',
      icon: Database,
      steps: processingSteps.filter(step => step.category === 'sku_processing')
    },
    {
      id: 'user_actions',
      title: 'User Actions Required',
      icon: User,
      steps: processingSteps.filter(step => step.category === 'user_interaction')
    },
    {
      id: 'system_processes',
      title: 'System Processes',
      icon: Settings,
      steps: processingSteps.filter(step => step.category === 'system_process')
    }
  ];

  const filteredSections = processingSections.map(section => ({
    ...section,
    steps: section.steps.filter(step => {
      const matchesSearch = step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           step.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterStatus === 'all' || step.status === filterStatus;
      return matchesSearch && matchesFilter;
    })
  })).filter(section => section.steps.length > 0);

  const renderStepActions = (step) => {
    const actions = [];
    
    // Based on step status, show relevant actions
    switch (step.status) {
      case 'pending':
        actions.push(
          <button
            key="start"
            onClick={() => executeAction('restart', step.id)}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Play className="w-4 h-4" />
            <span>Start</span>
          </button>
        );
        break;
      
      case 'running':
        actions.push(
          <button
            key="pause"
            onClick={() => executeAction('pause', step.id)}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600"
          >
            <Pause className="w-4 h-4" />
            <span>Pause</span>
          </button>
        );
        break;
      
      case 'failed':
        actions.push(
          <button
            key="retry"
            onClick={() => executeAction('retry', step.id)}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        );
        break;
      
      case 'paused':
        actions.push(
          <button
            key="resume"
            onClick={() => executeAction('resume', step.id)}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Play className="w-4 h-4" />
            <span>Resume</span>
          </button>
        );
        break;
      
      case 'waiting_user':
        actions.push(
          <button
            key="edit"
            onClick={() => executeAction('take_action', step.id)}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600"
          >
            <Edit className="w-4 h-4" />
            <span>Take Action</span>
          </button>
        );
        break;
      
      default:
        // No additional actions for completed or unknown status
        break;
    }

    // Common actions for all steps
    actions.push(
      <button
        key="view"
        onClick={() => executeAction('view_details', step.id)}
        className="flex items-center space-x-1 px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
      >
        <Eye className="w-4 h-4" />
        <span>View</span>
      </button>
    );

    if (step.category === 'communication') {
      actions.push(
        <button
          key="send"
          onClick={() => executeAction('send_email', step.id)}
          className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      );
    }

    return actions;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading processing steps...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Order Processing Menu</h1>
              <p className="text-sm text-gray-600">Order ID: {orderId}</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={loadProcessingSteps}
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

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search steps..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="paused">Paused</option>
                <option value="waiting_user">Waiting for User</option>
              </select>
            </div>
          </div>
        </div>

        {/* Processing Sections */}
        <div className="space-y-6">
          {filteredSections.map((section) => (
            <div key={section.id} className="bg-white rounded-lg shadow">
              <div
                className="px-6 py-4 border-b cursor-pointer hover:bg-gray-50"
                onClick={() => toggleSection(section.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <section.icon className="w-6 h-6 text-gray-600" />
                    <h3 className="text-lg font-medium text-gray-900">{section.title}</h3>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {section.steps.length} steps
                    </span>
                  </div>
                  {expandedSections[section.id] ? (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {expandedSections[section.id] && (
                <div className="p-6">
                  <div className="space-y-4">
                    {section.steps.map((step) => (
                      <div key={step.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0 mt-1">
                              {getStepIcon(step.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2">
                                <h4 className="text-sm font-medium text-gray-900">{step.name}</h4>
                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(step.status)}`}>
                                  {step.status.replace('_', ' ')}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                              {step.last_updated && (
                                <p className="text-xs text-gray-500 mt-1 flex items-center">
                                  <Clock className="w-3 h-3 mr-1" />
                                  Last updated: {new Date(step.last_updated).toLocaleString()}
                                </p>
                              )}
                              {step.error_message && (
                                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                                  <p className="text-sm text-red-700">{step.error_message}</p>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {renderStepActions(step)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {filteredSections.length === 0 && (
          <div className="text-center py-12">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No processing steps found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderProcessingMenu;
