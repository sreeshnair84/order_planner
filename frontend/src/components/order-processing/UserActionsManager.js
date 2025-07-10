import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  Edit,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  X,
  Eye,
  Search,
  Filter,
  FileText,
  Mail,
  Upload,
  Download,
  Settings,
  ChevronRight,
  ChevronDown
} from 'lucide-react';

const UserActionsManager = ({ orderId, onClose }) => {
  const [userActions, setUserActions] = useState([]);
  const [selectedAction, setSelectedAction] = useState(null);
  const [showActionModal, setShowActionModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [expandedActions, setExpandedActions] = useState({});

  const loadUserActions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/requestedorders/${orderId}/user-actions`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserActions(data.data || []);
      }
    } catch (error) {
      console.error('Error loading user actions:', error);
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      loadUserActions();
    }
  }, [orderId, loadUserActions]);

  const handleUserAction = async (action, actionId, params = {}) => {
    try {
      const endpoint = getUserActionEndpoint(action, actionId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ orderId, actionId, ...params })
      });

      if (response.ok) {
        await loadUserActions();
        return await response.json();
      } else {
        throw new Error(`User action failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error executing user action ${action}:`, error);
      throw error;
    }
  };

  const getUserActionEndpoint = (action, actionId) => {
    const endpoints = {
      'complete': `/api/requestedorders/${orderId}/complete-user-action`,
      'skip': `/api/requestedorders/${orderId}/skip-user-action`,
      'defer': `/api/requestedorders/${orderId}/defer-user-action`,
      'correct_missing_fields': `/api/requestedorders/${orderId}/correct-missing-fields`,
      'correct_validation_errors': `/api/requestedorders/${orderId}/correct-validation-errors`,
      'approve_changes': `/api/requestedorders/${orderId}/approve-changes`,
      'reject_changes': `/api/requestedorders/${orderId}/reject-changes`,
      'provide_feedback': `/api/requestedorders/${orderId}/provide-feedback`,
      'upload_file': `/api/requestedorders/${orderId}/upload-correction-file`,
      'download_template': `/api/requestedorders/${orderId}/download-correction-template`
    };
    return endpoints[action] || `/api/requestedorders/${orderId}/generic-user-action`;
  };

  const openActionModal = (action, actionData = null) => {
    setSelectedAction({ type: action, data: actionData });
    setShowActionModal(true);
  };

  const closeActionModal = () => {
    setShowActionModal(false);
    setSelectedAction(null);
  };

  const toggleActionExpansion = (actionId) => {
    setExpandedActions(prev => ({
      ...prev,
      [actionId]: !prev[actionId]
    }));
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'high': 'bg-red-100 text-red-800 border-red-200',
      'medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'low': 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[priority] || colors.medium;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'in_progress':
        return <RefreshCw className="w-4 h-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'skipped':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    }
  };

  const getActionTypeIcon = (type) => {
    const icons = {
      'correct_missing_fields': Edit,
      'correct_validation_errors': AlertTriangle,
      'approve_changes': CheckCircle,
      'provide_feedback': Mail,
      'upload_file': Upload,
      'review_data': Eye,
      'manual_entry': FileText,
      'confirm_details': CheckCircle,
      'select_option': Settings
    };
    const IconComponent = icons[type] || User;
    return <IconComponent className="w-5 h-5" />;
  };

  const filteredActions = userActions.filter(action => {
    const matchesSearch = action.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         action.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPriority = filterPriority === 'all' || action.priority === filterPriority;
    const matchesStatus = filterStatus === 'all' || action.status === filterStatus;
    return matchesSearch && matchesPriority && matchesStatus;
  });

  const actionsByCategory = {
    'data_correction': filteredActions.filter(action => action.category === 'data_correction'),
    'validation': filteredActions.filter(action => action.category === 'validation'),
    'approval': filteredActions.filter(action => action.category === 'approval'),
    'communication': filteredActions.filter(action => action.category === 'communication'),
    'file_management': filteredActions.filter(action => action.category === 'file_management'),
    'review': filteredActions.filter(action => action.category === 'review')
  };

  const categoryInfo = {
    'data_correction': {
      title: 'Data Corrections',
      icon: Edit,
      description: 'Fix missing or incorrect data fields'
    },
    'validation': {
      title: 'Validation Issues',
      icon: AlertTriangle,
      description: 'Resolve validation errors and conflicts'
    },
    'approval': {
      title: 'Approvals Required',
      icon: CheckCircle,
      description: 'Review and approve changes or decisions'
    },
    'communication': {
      title: 'Communications',
      icon: Mail,
      description: 'Send emails and communicate with stakeholders'
    },
    'file_management': {
      title: 'File Management',
      icon: Upload,
      description: 'Upload, download, and manage files'
    },
    'review': {
      title: 'Review Tasks',
      icon: Eye,
      description: 'Review data and processing results'
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading user actions...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">User Actions Required</h1>
              <p className="text-sm text-gray-600">Order ID: {orderId}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Pending:</span>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
                  {filteredActions.filter(a => a.status === 'pending').length}
                </span>
              </div>
              <button
                onClick={loadUserActions}
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

      {/* Quick Actions */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <button
              onClick={() => openActionModal('correct_missing_fields')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Edit className="w-6 h-6 text-blue-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Correct Missing Fields</span>
            </button>
            <button
              onClick={() => openActionModal('correct_validation_errors')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <AlertTriangle className="w-6 h-6 text-yellow-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Fix Validation Errors</span>
            </button>
            <button
              onClick={() => openActionModal('upload_file')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Upload className="w-6 h-6 text-green-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Upload Correction File</span>
            </button>
            <button
              onClick={() => openActionModal('download_template')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Download className="w-6 h-6 text-purple-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Download Template</span>
            </button>
            <button
              onClick={() => openActionModal('provide_feedback')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Mail className="w-6 h-6 text-indigo-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Provide Feedback</span>
            </button>
            <button
              onClick={() => openActionModal('review_all')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              <Eye className="w-6 h-6 text-gray-600 mb-2" />
              <span className="text-sm text-gray-700 text-center">Review All</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search actions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Priority</option>
                <option value="high">High Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="low">Low Priority</option>
              </select>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="skipped">Skipped</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Categories */}
        <div className="space-y-6">
          {Object.entries(actionsByCategory).map(([categoryId, actions]) => {
            if (actions.length === 0) return null;
            
            const category = categoryInfo[categoryId];
            return (
              <div key={categoryId} className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b">
                  <div className="flex items-center space-x-3">
                    <category.icon className="w-6 h-6 text-gray-600" />
                    <h3 className="text-lg font-medium text-gray-900">{category.title}</h3>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {actions.length} actions
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                </div>

                <div className="p-6">
                  <div className="space-y-4">
                    {actions.map((action) => (
                      <div key={action.id} className="border rounded-lg">
                        <div className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3">
                              <div className="flex-shrink-0 mt-1">
                                {getActionTypeIcon(action.type)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2">
                                  <h4 className="text-sm font-medium text-gray-900">{action.title}</h4>
                                  <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(action.priority)}`}>
                                    {action.priority}
                                  </span>
                                  <div className="flex items-center space-x-1">
                                    {getStatusIcon(action.status)}
                                    <span className="text-xs text-gray-600">{action.status}</span>
                                  </div>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                  <div className="flex items-center space-x-1">
                                    <Clock className="w-3 h-3" />
                                    <span>Created: {new Date(action.created_at).toLocaleString()}</span>
                                  </div>
                                  {action.due_date && (
                                    <div className="flex items-center space-x-1">
                                      <AlertTriangle className="w-3 h-3" />
                                      <span>Due: {new Date(action.due_date).toLocaleString()}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => toggleActionExpansion(action.id)}
                                className="p-1 text-gray-400 hover:text-gray-600"
                              >
                                {expandedActions[action.id] ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </button>
                              <button
                                onClick={() => openActionModal(action.type, action)}
                                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                              >
                                Take Action
                              </button>
                              {action.status === 'pending' && (
                                <button
                                  onClick={() => handleUserAction('skip', action.id)}
                                  className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
                                >
                                  Skip
                                </button>
                              )}
                            </div>
                          </div>
                        </div>

                        {expandedActions[action.id] && (
                          <div className="border-t px-4 py-3 bg-gray-50">
                            <div className="space-y-2">
                              {action.details && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-900">Details:</h5>
                                  <p className="text-sm text-gray-600">{action.details}</p>
                                </div>
                              )}
                              {action.current_data && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-900">Current Data:</h5>
                                  <pre className="text-xs text-gray-600 bg-gray-100 p-2 rounded mt-1">
                                    {JSON.stringify(action.current_data, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {action.expected_format && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-900">Expected Format:</h5>
                                  <p className="text-sm text-gray-600">{action.expected_format}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {filteredActions.length === 0 && (
          <div className="text-center py-12">
            <User className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No user actions found matching your criteria.</p>
          </div>
        )}
      </div>

      {/* Action Modal */}
      {showActionModal && (
        <UserActionModal
          action={selectedAction}
          orderId={orderId}
          onClose={closeActionModal}
          onComplete={loadUserActions}
        />
      )}
    </div>
  );
};

const UserActionModal = ({ action, orderId, onClose, onComplete }) => {
  const [formData, setFormData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [files, setFiles] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('orderId', orderId);
      formDataToSend.append('actionType', action.type);
      formDataToSend.append('data', JSON.stringify(formData));
      
      files.forEach((file, index) => {
        formDataToSend.append(`file_${index}`, file);
      });
      
      const response = await fetch(`/api/requestedorders/${orderId}/complete-user-action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formDataToSend
      });

      if (response.ok) {
        await onComplete();
        onClose();
      }
    } catch (error) {
      console.error('Error completing user action:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderActionForm = () => {
    switch (action.type) {
      case 'correct_missing_fields':
        return (
          <div className="space-y-4">
            <h4 className="font-medium">Correct Missing Fields</h4>
            <div className="space-y-3">
              {action.data?.missing_fields?.map((field, index) => (
                <div key={index}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.name} *
                  </label>
                  <input
                    type={field.type || 'text'}
                    value={formData[field.name] || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={field.placeholder || `Enter ${field.name}`}
                  />
                  {field.description && (
                    <p className="text-xs text-gray-500 mt-1">{field.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'upload_file':
        return (
          <div className="space-y-4">
            <h4 className="font-medium">Upload Correction File</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select File
              </label>
              <input
                type="file"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        );
      
      case 'provide_feedback':
        return (
          <div className="space-y-4">
            <h4 className="font-medium">Provide Feedback</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Feedback
              </label>
              <textarea
                value={formData.feedback || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, feedback: e.target.value }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your feedback..."
              />
            </div>
          </div>
        );
      
      default:
        return (
          <div className="space-y-4">
            <h4 className="font-medium">Action Details</h4>
            <p className="text-sm text-gray-600">
              Complete the action: {action.data?.title || action.type}
            </p>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                User Action Required
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              {renderActionForm()}
              
              <div className="flex justify-end space-x-3 pt-6 mt-6 border-t">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {isSubmitting ? 'Processing...' : 'Complete Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserActionsManager;
