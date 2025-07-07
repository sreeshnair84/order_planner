import React, { useState, useEffect, useCallback } from 'react';
import {
  Mail,
  Send,
  Eye,
  Edit,
  Plus,
  RefreshCw,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Copy,
  Search,
  Filter,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

const EmailCommunicationsManager = ({ orderId, onClose }) => {
  const [emails, setEmails] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailAction, setEmailAction] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [expandedEmails, setExpandedEmails] = useState({});

  const loadEmailData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [emailsResponse, templatesResponse] = await Promise.all([
        fetch(`/api/orders/${orderId}/emails`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/email-templates`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (emailsResponse.ok) {
        const emailsData = await emailsResponse.json();
        setEmails(emailsData.data?.emails || []);
      }

      if (templatesResponse.ok) {
        const templatesData = await templatesResponse.json();
        setTemplates(templatesData.data || []);
      }
    } catch (error) {
      console.error('Error loading email data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      loadEmailData();
    }
  }, [orderId, loadEmailData]);

  const handleEmailAction = async (action, emailId, params = {}) => {
    try {
      const endpoint = getEmailActionEndpoint(action, emailId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ orderId, emailId, ...params })
      });

      if (response.ok) {
        const result = await response.json();
        await loadEmailData();
        return result;
      } else {
        throw new Error(`Email action failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error executing email action ${action}:`, error);
      throw error;
    }
  };

  const getEmailActionEndpoint = (action, emailId) => {
    const endpoints = {
      'send': `/api/orders/${orderId}/send-email`,
      'resend': `/api/orders/${orderId}/resend-email`,
      'edit': `/api/orders/${orderId}/edit-email`,
      'delete': `/api/orders/${orderId}/delete-email`,
      'duplicate': `/api/orders/${orderId}/duplicate-email`,
      'view': `/api/orders/${orderId}/view-email`,
      'download': `/api/orders/${orderId}/download-email`,
      'generate': `/api/orders/${orderId}/generate-email`
    };
    return endpoints[action] || `/api/orders/${orderId}/email-action`;
  };

  const openEmailModal = (action, email = null) => {
    setEmailAction(action);
    setSelectedEmail(email);
    setShowEmailModal(true);
  };

  const closeEmailModal = () => {
    setShowEmailModal(false);
    setEmailAction(null);
    setSelectedEmail(null);
  };

  const toggleEmailExpansion = (emailId) => {
    setExpandedEmails(prev => ({
      ...prev,
      [emailId]: !prev[emailId]
    }));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'draft':
        return <FileText className="w-4 h-4 text-gray-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'sent': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'draft': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredEmails = emails.filter(email => {
    const matchesSearch = email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         email.recipient.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         email.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || email.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const emailTypes = [
    { id: 'missing_info', label: 'Missing Information', icon: AlertTriangle },
    { id: 'validation_failed', label: 'Validation Failed', icon: XCircle },
    { id: 'catalog_mismatch', label: 'Catalog Mismatch', icon: FileText },
    { id: 'data_quality', label: 'Data Quality Issues', icon: AlertTriangle },
    { id: 'order_confirmation', label: 'Order Confirmation', icon: CheckCircle },
    { id: 'custom', label: 'Custom Email', icon: Mail }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading email communications...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">Email Communications</h1>
              <p className="text-sm text-gray-600">Order ID: {orderId}</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => openEmailModal('generate')}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                <Plus className="w-4 h-4" />
                <span>Generate Email</span>
              </button>
              <button
                onClick={loadEmailData}
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
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Email Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {emailTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => openEmailModal('generate', { type: type.id })}
                className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
              >
                <type.icon className="w-6 h-6 text-gray-600 mb-2" />
                <span className="text-sm text-gray-700 text-center">{type.label}</span>
              </button>
            ))}
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
                  placeholder="Search emails..."
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
                <option value="sent">Sent</option>
                <option value="pending">Pending</option>
                <option value="draft">Draft</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Email List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Email History</h3>
              <span className="text-sm text-gray-500">{filteredEmails.length} emails</span>
            </div>
            
            {filteredEmails.length === 0 ? (
              <div className="text-center py-12">
                <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No emails found matching your criteria.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredEmails.map((email) => (
                  <div key={email.id} className="border rounded-lg">
                    <div className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 mt-1">
                            {getStatusIcon(email.status)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <h4 className="text-sm font-medium text-gray-900">{email.subject}</h4>
                              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(email.status)}`}>
                                {email.status}
                              </span>
                              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                                {email.type}
                              </span>
                            </div>
                            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                              <div className="flex items-center space-x-1">
                                <User className="w-3 h-3" />
                                <span>{email.recipient}</span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <Clock className="w-3 h-3" />
                                <span>{new Date(email.created_at).toLocaleString()}</span>
                              </div>
                            </div>
                            {email.error_message && (
                              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                                <p className="text-sm text-red-700">{email.error_message}</p>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => toggleEmailExpansion(email.id)}
                            className="p-1 text-gray-400 hover:text-gray-600"
                          >
                            {expandedEmails[email.id] ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronRight className="w-4 h-4" />
                            )}
                          </button>
                          <button
                            onClick={() => openEmailModal('view', email)}
                            className="p-1 text-blue-500 hover:text-blue-600"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => openEmailModal('edit', email)}
                            className="p-1 text-yellow-500 hover:text-yellow-600"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          {email.status === 'draft' && (
                            <button
                              onClick={() => handleEmailAction('send', email.id)}
                              className="p-1 text-green-500 hover:text-green-600"
                            >
                              <Send className="w-4 h-4" />
                            </button>
                          )}
                          {email.status === 'sent' && (
                            <button
                              onClick={() => handleEmailAction('resend', email.id)}
                              className="p-1 text-orange-500 hover:text-orange-600"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleEmailAction('duplicate', email.id)}
                            className="p-1 text-purple-500 hover:text-purple-600"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {expandedEmails[email.id] && (
                      <div className="border-t px-4 py-3 bg-gray-50">
                        <div className="prose prose-sm max-w-none">
                          <div dangerouslySetInnerHTML={{ __html: email.html_content || email.text_content }} />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Email Modal */}
      {showEmailModal && (
        <EmailActionModal
          action={emailAction}
          email={selectedEmail}
          orderId={orderId}
          templates={templates}
          onClose={closeEmailModal}
          onComplete={loadEmailData}
        />
      )}
    </div>
  );
};

const EmailActionModal = ({ action, email, orderId, templates, onClose, onComplete }) => {
  const [formData, setFormData] = useState({
    subject: '',
    recipient: '',
    type: 'missing_info',
    template: '',
    html_content: '',
    text_content: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (email) {
      setFormData({
        subject: email.subject || '',
        recipient: email.recipient || '',
        type: email.type || 'missing_info',
        template: email.template || '',
        html_content: email.html_content || '',
        text_content: email.text_content || ''
      });
    }
  }, [email]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const endpoint = action === 'generate' 
        ? `/api/orders/${orderId}/generate-email`
        : `/api/orders/${orderId}/update-email`;
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...formData,
          emailId: email?.id
        })
      });

      if (response.ok) {
        await onComplete();
        onClose();
      }
    } catch (error) {
      console.error('Error submitting email:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const actionTitles = {
    'generate': 'Generate New Email',
    'edit': 'Edit Email',
    'view': 'View Email'
  };

  const isReadOnly = action === 'view';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {actionTitles[action]}
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Type
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                    disabled={isReadOnly}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="missing_info">Missing Information</option>
                    <option value="validation_failed">Validation Failed</option>
                    <option value="catalog_mismatch">Catalog Mismatch</option>
                    <option value="data_quality">Data Quality Issues</option>
                    <option value="order_confirmation">Order Confirmation</option>
                    <option value="custom">Custom Email</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template
                  </label>
                  <select
                    value={formData.template}
                    onChange={(e) => setFormData(prev => ({ ...prev, template: e.target.value }))}
                    disabled={isReadOnly}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select template...</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recipient
                </label>
                <input
                  type="email"
                  value={formData.recipient}
                  onChange={(e) => setFormData(prev => ({ ...prev, recipient: e.target.value }))}
                  disabled={isReadOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter recipient email"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                  disabled={isReadOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter email subject"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Content
                </label>
                <textarea
                  value={formData.html_content}
                  onChange={(e) => setFormData(prev => ({ ...prev, html_content: e.target.value }))}
                  disabled={isReadOnly}
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter email content (HTML supported)"
                />
              </div>

              {!isReadOnly && (
                <div className="flex justify-end space-x-3 pt-4">
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
                    {isSubmitting ? 'Processing...' : action === 'generate' ? 'Generate' : 'Update'}
                  </button>
                </div>
              )}
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailCommunicationsManager;
