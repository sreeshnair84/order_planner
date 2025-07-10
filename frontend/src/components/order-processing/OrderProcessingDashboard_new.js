import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Mail, AlertCircle, CheckCircle, XCircle, RefreshCw, Edit, Send, X, Eye, ThumbsUp } from 'lucide-react';
import { orderProcessingService } from '../../services/orderProcessingService';
import ActionModal from './ActionModal';

const OrderProcessingDashboard = ({ orderId }) => {
  const [orderDetails, setOrderDetails] = useState(null);
  const [trackingHistory, setTrackingHistory] = useState([]);
  const [validationSummary, setValidationSummary] = useState(null);
  const [emailCommunications, setEmailCommunications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tracking');
  const [selectedAction, setSelectedAction] = useState(null);
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);

  const loadOrderData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Load all order data in parallel
      const [trackingData, validationData, emailsData] = await Promise.all([
        orderProcessingService.getOrderTracking(orderId),
        orderProcessingService.getOrderValidationSummary(orderId),
        orderProcessingService.getOrderEmails(orderId)
      ]);

      setTrackingHistory(trackingData.tracking_history || []);
      setOrderDetails(trackingData.order_details || {});
      setValidationSummary(validationData);
      setEmailCommunications(emailsData.emails || []);
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
      await orderProcessingService.restartFromCheckpoint(orderId, checkpointStatus);
      await loadOrderData(); // Refresh data
      alert('Process restarted successfully from checkpoint');
    } catch (error) {
      console.error('Error restarting from checkpoint:', error);
      alert('Error restarting from checkpoint');
    }
  };

  const handleRetriggerJob = async (jobType) => {
    try {
      await orderProcessingService.retriggerJob(orderId, jobType);
      await loadOrderData(); // Refresh data
      alert(`${jobType} job retriggered successfully`);
    } catch (error) {
      console.error(`Error retriggering ${jobType}:`, error);
      alert(`Error retriggering ${jobType} job`);
    }
  };

  const handleApproveEmail = async (emailId) => {
    try {
      await orderProcessingService.approveEmail(orderId, emailId);
      await loadOrderData(); // Refresh data
      alert('Email approved and sent successfully');
    } catch (error) {
      console.error('Error approving email:', error);
      alert('Error approving email');
    }
  };

  const handlePreviewEmail = (email) => {
    setSelectedEmail(email);
    setShowEmailPreview(true);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const renderTrackingTab = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Processing Timeline</h3>
        <div className="space-y-3">
          {trackingHistory.map((step, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              {getStatusIcon(step.status)}
              <div className="flex-1">
                <div className="font-medium">{step.step_name}</div>
                <div className="text-sm text-gray-600">{step.description}</div>
                <div className="text-xs text-gray-500">
                  {step.started_at && `Started: ${new Date(step.started_at).toLocaleString()}`}
                  {step.completed_at && ` | Completed: ${new Date(step.completed_at).toLocaleString()}`}
                </div>
              </div>
              {step.status === 'failed' && (
                <button
                  onClick={() => handleRestartFromCheckpoint(step.step_name)}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  Restart
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderValidationTab = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Validation Results</h3>
          <button
            onClick={() => handleRetriggerJob('validation')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Revalidate</span>
          </button>
        </div>
        
        {validationSummary && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="font-medium text-green-800">Valid Items</div>
                <div className="text-2xl font-bold text-green-600">
                  {validationSummary.valid_items || 0}
                </div>
              </div>
              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="font-medium text-yellow-800">Warnings</div>
                <div className="text-2xl font-bold text-yellow-600">
                  {validationSummary.warnings || 0}
                </div>
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <div className="font-medium text-red-800">Errors</div>
                <div className="text-2xl font-bold text-red-600">
                  {validationSummary.errors || 0}
                </div>
              </div>
            </div>
            
            {validationSummary.validation_details && (
              <div>
                <h4 className="font-medium mb-2">Validation Details</h4>
                <div className="space-y-2">
                  {validationSummary.validation_details.map((detail, index) => (
                    <div key={index} className={`p-3 rounded-lg ${
                      detail.level === 'error' ? 'bg-red-50 border border-red-200' :
                      detail.level === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                      'bg-green-50 border border-green-200'
                    }`}>
                      <div className="font-medium">{detail.field || 'General'}</div>
                      <div className="text-sm">{detail.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderEmailsTab = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Email Communications</h3>
          <button
            onClick={() => handleRetriggerJob('email_generation')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center space-x-2"
          >
            <Mail className="h-4 w-4" />
            <span>Generate Email</span>
          </button>
        </div>
        
        <div className="space-y-3">
          {emailCommunications.map((email, index) => (
            <div key={index} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="font-medium">{email.subject}</div>
                  <div className="text-sm text-gray-600">
                    To: {email.recipient} | Type: {email.type}
                  </div>
                  <div className="text-xs text-gray-500">
                    {email.created_at && `Created: ${new Date(email.created_at).toLocaleString()}`}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handlePreviewEmail(email)}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 flex items-center space-x-1"
                  >
                    <Eye className="h-3 w-3" />
                    <span>Preview</span>
                  </button>
                  {email.status === 'draft' && (
                    <button
                      onClick={() => handleApproveEmail(email.id)}
                      className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 flex items-center space-x-1"
                    >
                      <ThumbsUp className="h-3 w-3" />
                      <span>Approve</span>
                    </button>
                  )}
                </div>
              </div>
              <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                {email.preview || email.content?.substring(0, 150) + '...'}
              </div>
            </div>
          ))}
        </div>
        
        {emailCommunications.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No email communications found for this order.
          </div>
        )}
      </div>
    </div>
  );

  const renderEmailPreview = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">Email Preview</h3>
          <button
            onClick={() => setShowEmailPreview(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {selectedEmail && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Subject</label>
                <div className="mt-1 p-2 bg-gray-50 rounded">{selectedEmail.subject}</div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">To</label>
                <div className="mt-1 p-2 bg-gray-50 rounded">{selectedEmail.recipient}</div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Content</label>
                <div className="mt-1 p-4 bg-gray-50 rounded whitespace-pre-wrap">
                  {selectedEmail.content}
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-3 p-4 border-t">
          <button
            onClick={() => setShowEmailPreview(false)}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
          >
            Close
          </button>
          {selectedEmail?.status === 'draft' && (
            <button
              onClick={() => {
                handleApproveEmail(selectedEmail.id);
                setShowEmailPreview(false);
              }}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center space-x-2"
            >
              <ThumbsUp className="h-4 w-4" />
              <span>Approve & Send</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading order data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Order Summary Header */}
      {orderDetails && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-semibold">Order #{orderDetails.id}</h2>
              <div className="text-sm text-gray-600 mt-1">
                Status: <span className="font-medium">{orderDetails.status}</span>
                {orderDetails.created_at && (
                  <span className="ml-4">
                    Created: {new Date(orderDetails.created_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handleRetriggerJob('full_processing')}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center space-x-2"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Reprocess</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'tracking', label: 'Processing Timeline', icon: Clock },
              { id: 'validation', label: 'Validation', icon: CheckCircle },
              { id: 'emails', label: 'Communications', icon: Mail }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'tracking' && renderTrackingTab()}
          {activeTab === 'validation' && renderValidationTab()}
          {activeTab === 'emails' && renderEmailsTab()}
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

      {/* Email Preview Modal */}
      {showEmailPreview && renderEmailPreview()}
    </div>
  );
};

export default OrderProcessingDashboard;
