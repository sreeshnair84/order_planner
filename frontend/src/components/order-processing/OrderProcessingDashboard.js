import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Mail, AlertCircle, CheckCircle, XCircle, RefreshCw, Edit, Send } from 'lucide-react';
import { getApiUrl } from '../../utils/apiConfig';
import ActionModal from './ActionModal';

const OrderProcessingDashboard = ({ orderId }) => {
  const [orderDetails, setOrderDetails] = useState(null);
  const [trackingHistory, setTrackingHistory] = useState([]);
  const [validationSummary, setValidationSummary] = useState(null);
  const [emailCommunications, setEmailCommunications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tracking');
  const [selectedAction, setSelectedAction] = useState(null);

  const loadOrderData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Load all order data in parallel
      const [trackingResponse, validationResponse, emailsResponse] = await Promise.all([
        fetch(getApiUrl(`api/orders/${orderId}/tracking`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(getApiUrl(`api/orders/${orderId}/validation-summary`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(getApiUrl(`api/orders/${orderId}/emails`), {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      const trackingData = await trackingResponse.json();
      const validationData = await validationResponse.json();
      const emailsData = await emailsResponse.json();

      setTrackingHistory(trackingData.data?.tracking_history || []);
      setValidationSummary(validationData.data || null);
      setEmailCommunications(emailsData.data?.emails || []);
      setOrderDetails(validationData.data);
    } catch (error) {
      console.error('Error loading order data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      loadOrderData();
    }
  }, [orderId, loadOrderData]);

  const handleRestartFromCheckpoint = async (checkpointStatus) => {
    try {
      const response = await fetch(getApiUrl(`api/orders/${orderId}/restart-checkpoint`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ checkpoint: checkpointStatus })
      });

      if (response.ok) {
        await loadOrderData(); // Refresh data
        alert('Process restarted successfully from checkpoint');
      }
    } catch (error) {
      console.error('Error restarting from checkpoint:', error);
      alert('Error restarting process');
    }
  };

  const handleRetriggerJob = async (jobType) => {
    try {
      const endpoint = {
        'file_parsing': `/api/orders/${orderId}/parse-file`,
        'validation': `/api/orders/${orderId}/validate`,
        'email_generation': `/api/orders/${orderId}/generate-email`,
        'full_processing': `/api/orders/${orderId}/process`
      }[jobType];

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        await loadOrderData(); // Refresh data
        alert(`${jobType} job retriggered successfully`);
      }
    } catch (error) {
      console.error(`Error retriggering ${jobType}:`, error);
      alert(`Error retriggering ${jobType} job`);
    }
  };

  const getStatusIcon = (status, category) => {
    if (status.includes('ERROR') || status.includes('FAILED')) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    } else if (status.includes('COMPLETED') || status.includes('PASSED')) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status.includes('STARTED') || status.includes('PROGRESS')) {
      return <Clock className="w-5 h-5 text-blue-500" />;
    } else {
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'file_processing': 'bg-blue-100 text-blue-800',
      'validation': 'bg-yellow-100 text-yellow-800',
      'communication': 'bg-green-100 text-green-800',
      'processing': 'bg-purple-100 text-purple-800',
      'sku_processing': 'bg-indigo-100 text-indigo-800',
      'error': 'bg-red-100 text-red-800',
      'general': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.general;
  };

  const renderTrackingTimeline = () => (
    <div className="space-y-4">
      {trackingHistory.map((entry, index) => (
        <div key={entry.id} className="flex items-start space-x-4 p-4 bg-white rounded-lg border">
          <div className="flex-shrink-0">
            {getStatusIcon(entry.status, entry.category)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-medium text-gray-900">{entry.status}</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(entry.category)}`}>
                  {entry.category.replace('_', ' ')}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {new Date(entry.timestamp).toLocaleString()}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{entry.message}</p>
            {entry.details && (
              <details className="mt-2">
                <summary className="text-xs text-blue-600 cursor-pointer">Show details</summary>
                <pre className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded">{entry.details}</pre>
              </details>
            )}
            
            {/* Action buttons for failed or incomplete steps */}
            {(entry.status.includes('ERROR') || entry.status.includes('FAILED')) && (
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={() => handleRestartFromCheckpoint(entry.status)}
                  className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Restart from here</span>
                </button>
                <button
                  onClick={() => {
                    const jobType = entry.category === 'file_processing' ? 'file_parsing' :
                                   entry.category === 'validation' ? 'validation' :
                                   entry.category === 'communication' ? 'email_generation' : 'full_processing';
                    handleRetriggerJob(jobType);
                  }}
                  className="flex items-center space-x-1 px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Retry</span>
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  const renderValidationSummary = () => {
    if (!validationSummary?.validation_result) {
      return <div className="text-center text-gray-500 py-8">No validation data available</div>;
    }

    const validation = validationSummary.validation_result;
    const isValid = validation.is_valid;
    const score = validation.validation_score || 0;

    return (
      <div className="space-y-6">
        {/* Validation Overview */}
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Validation Status</h3>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              isValid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {isValid ? 'Valid' : 'Issues Found'}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{(score * 100).toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Validation Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{validation.missing_fields?.length || 0}</div>
              <div className="text-sm text-gray-600">Missing Fields</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{validation.validation_errors?.length || 0}</div>
              <div className="text-sm text-gray-600">Validation Errors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{validation.business_rule_violations?.length || 0}</div>
              <div className="text-sm text-gray-600">Rule Violations</div>
            </div>
          </div>
        </div>

        {/* Missing Fields */}
        {validation.missing_fields?.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-md font-semibold text-yellow-800">Missing Fields</h4>
              <button
                onClick={() => setSelectedAction({ type: 'correct_missing_fields', data: validation.missing_fields })}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600"
              >
                <Edit className="w-4 h-4" />
                <span>Correct Issues</span>
              </button>
            </div>
            <ul className="space-y-1">
              {validation.missing_fields.map((field, index) => (
                <li key={index} className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm text-yellow-800">{field}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Validation Errors */}
        {validation.validation_errors?.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-md font-semibold text-red-800">Validation Errors</h4>
              <button
                onClick={() => setSelectedAction({ type: 'correct_validation_errors', data: validation.validation_errors })}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
              >
                <Edit className="w-4 h-4" />
                <span>Fix Errors</span>
              </button>
            </div>
            <ul className="space-y-1">
              {validation.validation_errors.map((error, index) => (
                <li key={index} className="flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <span className="text-sm text-red-800">{error}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Business Rule Violations */}
        {validation.business_rule_violations?.length > 0 && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-md font-semibold text-purple-800">Business Rule Violations</h4>
              <button
                onClick={() => setSelectedAction({ type: 'correct_business_rules', data: validation.business_rule_violations })}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600"
              >
                <Edit className="w-4 h-4" />
                <span>Review Rules</span>
              </button>
            </div>
            <ul className="space-y-1">
              {validation.business_rule_violations.map((violation, index) => (
                <li key={index} className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-purple-600" />
                  <span className="text-sm text-purple-800">{violation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button
            onClick={() => handleRetriggerJob('validation')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Re-validate Order</span>
          </button>
          {!isValid && (
            <button
              onClick={() => handleRetriggerJob('email_generation')}
              className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              <Mail className="w-4 h-4" />
              <span>Generate Email</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderEmailCommunications = () => (
    <div className="space-y-4">
      {emailCommunications.length === 0 ? (
        <div className="text-center text-gray-500 py-8">No email communications found</div>
      ) : (
        emailCommunications.map((email) => (
          <div key={email.id} className="bg-white p-6 rounded-lg border">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Mail className="w-5 h-5 text-blue-500" />
                <h3 className="text-lg font-semibold">{email.subject}</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  email.email_type === 'missing_info' ? 'bg-yellow-100 text-yellow-800' :
                  email.email_type === 'validation_failed' ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {email.email_type.replace('_', ' ')}
                </span>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setSelectedAction({ type: 'view_email', data: email })}
                  className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  View
                </button>
                <button
                  onClick={() => setSelectedAction({ type: 'resend_email', data: email })}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                >
                  <Send className="w-3 h-3" />
                  <span>Resend</span>
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
              <div>
                <span className="font-medium">To:</span> {email.recipient}
              </div>
              <div>
                <span className="font-medium">From:</span> {email.sender}
              </div>
              <div>
                <span className="font-medium">Created:</span> {new Date(email.created_at).toLocaleString()}
              </div>
              <div>
                <span className="font-medium">Status:</span> 
                <span className={`ml-1 px-2 py-1 text-xs rounded ${
                  email.sent_at ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {email.sent_at ? 'Sent' : 'Draft'}
                </span>
              </div>
            </div>

            {email.response_received_at && (
              <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-green-800">
                    Response received on {new Date(email.response_received_at).toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            <div className="bg-gray-50 rounded p-3">
              <div className="text-sm text-gray-600" dangerouslySetInnerHTML={{ __html: email.body?.substring(0, 200) + '...' }} />
            </div>
          </div>
        ))
      )}
      
      <div className="flex justify-center">
        <button
          onClick={() => handleRetriggerJob('email_generation')}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          <Mail className="w-4 h-4" />
          <span>Generate New Email</span>
        </button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading order processing data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Order Processing Dashboard</h1>
            {orderDetails && (
              <p className="text-gray-600">
                Order: {orderDetails.order_number} | Status: 
                <span className={`ml-1 px-2 py-1 text-xs rounded ${
                  orderDetails.current_status === 'VALIDATED' ? 'bg-green-100 text-green-800' :
                  orderDetails.current_status === 'MISSING_INFO' ? 'bg-yellow-100 text-yellow-800' :
                  orderDetails.current_status === 'VALIDATION_FAILED' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {orderDetails.current_status}
                </span>
              </p>
            )}
          </div>
          <button
            onClick={() => handleRetriggerJob('full_processing')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reprocess Order</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border">
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'tracking', label: 'Processing Timeline', icon: Clock },
              { id: 'validation', label: 'Validation Results', icon: AlertCircle },
              { id: 'communications', label: 'Email Communications', icon: Mail }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'tracking' && renderTrackingTimeline()}
          {activeTab === 'validation' && renderValidationSummary()}
          {activeTab === 'communications' && renderEmailCommunications()}
        </div>
      </div>

      {/* Action Modal */}
      {selectedAction && (
        <ActionModal
          action={selectedAction}
          orderId={orderId}
          onClose={() => setSelectedAction(null)}
          onSuccess={loadOrderData}
        />
      )}
    </div>
  );
};

export default OrderProcessingDashboard;
