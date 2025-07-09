import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import toast from 'react-hot-toast';
import { 
  Upload, 
  File, 
  Eye, 
  Play, 
  RotateCcw, 
  Settings, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  MessageSquare,
  Bot,
  Zap,
  Mail,
  FileText,
  Activity,
  Filter,
  Search,
  Download,
  RefreshCw,
  Package,
  Bell,
  MapPin,
  User
} from 'lucide-react';
import { orderService } from '../services/orderService';
import { aiAgentService } from '../services/aiAgentService';

const OrderProcessingScreen = ({ orderId, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedThread, setSelectedThread] = useState(null);
  const [showCreateThread, setShowCreateThread] = useState(false);
  const [newThreadMessage, setNewThreadMessage] = useState('');
  const [autoProcessing, setAutoProcessing] = useState(false);
  
  const queryClient = useQueryClient();

  // Queries
  const { data: orderDetails, isLoading: orderLoading, refetch: refetchOrder } = useQuery(
    ['order-details', orderId],
    () => orderService.getOrderDetails(orderId),
    {
      enabled: !!orderId,
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  const { data: aiThreads, isLoading: threadsLoading, refetch: refetchThreads } = useQuery(
    ['ai-threads', orderId],
    () => aiAgentService.getOrderThreads(orderId),
    {
      enabled: !!orderId,
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  );

  const { data: threadDetails } = useQuery(
    ['thread-details', selectedThread],
    () => aiAgentService.getThreadState(selectedThread),
    {
      enabled: !!selectedThread,
      refetchInterval: 3000, // Refresh every 3 seconds
    }
  );

  const { data: orderTracking } = useQuery(
    ['order-tracking', orderId],
    () => orderService.getOrderTracking(orderId),
    {
      enabled: !!orderId,
      refetchInterval: 5000,
    }
  );

  const { data: emailCommunications } = useQuery(
    ['email-communications', orderId],
    () => orderService.getEmailCommunications(orderId),
    {
      enabled: !!orderId,
      refetchInterval: 10000,
    }
  );

  const { data: orderSKUItems } = useQuery(
    ['order-sku-items', orderId],
    () => orderService.getOrderSKUItems(orderId),
    {
      enabled: !!orderId,
      refetchInterval: 10000,
    }
  );

  // Mutations
  const processOrderMutation = useMutation(
    () => orderService.processOrder(orderId),
    {
      onSuccess: () => {
        toast.success('Order processing started');
        refetchOrder();
      },
      onError: (error) => {
        toast.error(`Processing failed: ${error.message}`);
      }
    }
  );

  const reprocessOrderMutation = useMutation(
    () => orderService.reprocessOrder(orderId),
    {
      onSuccess: () => {
        toast.success('Order reprocessing started');
        refetchOrder();
      },
      onError: (error) => {
        toast.error(`Reprocessing failed: ${error.message}`);
      }
    }
  );

  const createAIThreadMutation = useMutation(
    ({ message, autoStart }) => aiAgentService.createThread(orderId, message, autoStart),
    {
      onSuccess: (data) => {
        toast.success('AI Agent thread created');
        setShowCreateThread(false);
        setNewThreadMessage('');
        refetchThreads();
        if (data.data.thread_id) {
          setSelectedThread(data.data.thread_id);
        }
      },
      onError: (error) => {
        toast.error(`Failed to create AI thread: ${error.message}`);
      }
    }
  );

  const runAIAgentMutation = useMutation(
    (threadId) => aiAgentService.runAgent(threadId),
    {
      onSuccess: () => {
        toast.success('AI Agent execution started');
        refetchThreads();
      },
      onError: (error) => {
        toast.error(`AI execution failed: ${error.message}`);
      }
    }
  );

  const processWithAIMutation = useMutation(
    () => aiAgentService.processOrderWithAI(orderId),
    {
      onSuccess: () => {
        toast.success('AI-powered processing started');
        setAutoProcessing(true);
        refetchOrder();
        refetchThreads();
      },
      onError: (error) => {
        toast.error(`AI processing failed: ${error.message}`);
        setAutoProcessing(false);
      }
    }
  );

  const uploadCorrectionMutation = useMutation(
    ({ file, emailId, errorType }) => orderService.uploadCorrection(file, orderId, errorType, emailId),
    {
      onSuccess: () => {
        toast.success('Corrected file uploaded successfully');
        refetchOrder();
        queryClient.invalidateQueries(['email-communications', orderId]);
        queryClient.invalidateQueries(['order-tracking', orderId]);
      },
      onError: (error) => {
        toast.error(`Upload failed: ${error.message}`);
      }
    }
  );

  // Status color mapping
  const getStatusColor = (status) => {
    const statusColors = {
      'UPLOADED': 'bg-blue-100 text-blue-800',
      'PROCESSING': 'bg-yellow-100 text-yellow-800',
      'PROCESSED': 'bg-green-100 text-green-800',
      'VALIDATION_FAILED': 'bg-red-100 text-red-800',
      'MISSING_INFO': 'bg-orange-100 text-orange-800',
      'COMPLETED': 'bg-green-100 text-green-800',
      'FAILED': 'bg-red-100 text-red-800',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const getThreadStatusIcon = (status) => {
    switch (status) {
      case 'CREATED': return <Clock className="h-4 w-4" />;
      case 'RUNNING': return <RefreshCw className="h-4 w-4 animate-spin" />;
      case 'COMPLETED': return <CheckCircle className="h-4 w-4" />;
      case 'FAILED': return <XCircle className="h-4 w-4" />;
      case 'TIMEOUT': return <AlertCircle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const handleCreateThread = () => {
    if (!newThreadMessage.trim()) {
      toast.error('Please enter a message for the AI agent');
      return;
    }
    
    createAIThreadMutation.mutate({
      message: newThreadMessage,
      autoStart: true
    });
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (orderLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg">Loading order details...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Order Processing Center</h2>
            <p className="text-blue-100">
              Order: {orderDetails?.order_number} | 
              Status: <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(orderDetails?.status)}`}>
                {orderDetails?.status}
              </span>
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoProcessing(!autoProcessing)}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
                autoProcessing 
                  ? 'bg-green-500 hover:bg-green-600' 
                  : 'bg-blue-500 hover:bg-blue-600'
              } transition-colors`}
            >
              <Bot className="h-4 w-4" />
              <span>{autoProcessing ? 'AI Active' : 'Enable AI'}</span>
            </button>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200"
            >
              <XCircle className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { id: 'overview', label: 'Overview', icon: Eye },
            { id: 'processing', label: 'Processing', icon: Settings },
            { id: 'sku-items', label: 'SKU Items', icon: Package },
            { id: 'ai-agent', label: 'AI Agent', icon: Bot },
            { id: 'tracking', label: 'Tracking', icon: Activity },
            { id: 'emails', label: 'Communications', icon: Mail }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Order Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <File className="h-5 w-5 text-gray-500" />
                  <h3 className="font-medium text-gray-900">File Details</h3>
                </div>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  
                  <p>Name: {orderDetails?.original_filename}</p>
                  <p>Type: {orderDetails?.file_type}</p>
                  <p>Size: {orderDetails?.file_size ? `${(orderDetails.file_size / 1024).toFixed(2)} KB` : 'N/A'}</p>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Package className="h-5 w-5 text-gray-500" />
                  <h3 className="font-medium text-gray-900">Order Summary</h3>
                </div>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  <p>Retailer: {orderDetails?.retailer_info?.name || 'N/A'}</p>
                  <p>Priority: <span className={`px-2 py-1 rounded text-xs font-medium ${
                    orderDetails?.priority === 'URGENT' ? 'bg-red-100 text-red-800' :
                    orderDetails?.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                    orderDetails?.priority === 'NORMAL' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>{orderDetails?.priority || 'NORMAL'}</span></p>
                  <p>SKUs: {orderDetails?.total_sku_count || 0}</p>
                  <p>Quantity: {orderDetails?.total_quantity || 0}</p>
                  <p>Weight: {orderDetails?.total_weight_kg || 0} kg</p>
                </div>
              </div>
              
              {/* Special Instructions */}
              {orderDetails?.special_instructions && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="h-5 w-5 text-amber-600" />
                    <h3 className="font-medium text-amber-900">Special Instructions</h3>
                  </div>
                  <div className="mt-2 text-sm text-amber-800">
                    {orderDetails.special_instructions}
                  </div>
                </div>
              )}
              
              {/* Delivery Information */}
              {orderDetails?.delivery_address && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-5 w-5 text-blue-600" />
                    <h3 className="font-medium text-blue-900">Delivery Information</h3>
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-blue-800">
                    {orderDetails.delivery_address.street && (
                      <p>{orderDetails.delivery_address.street}</p>
                    )}
                    {(orderDetails.delivery_address.city || orderDetails.delivery_address.state || orderDetails.delivery_address.zip_code) && (
                      <p>
                        {orderDetails.delivery_address.city && `${orderDetails.delivery_address.city}, `}
                        {orderDetails.delivery_address.state && `${orderDetails.delivery_address.state} `}
                        {orderDetails.delivery_address.zip_code}
                      </p>
                    )}
                    {orderDetails.delivery_address.country && (
                      <p>{orderDetails.delivery_address.country}</p>
                    )}
                    {orderDetails?.requested_delivery_date && (
                      <p className="mt-2 font-medium">
                        Requested Delivery: {formatDateTime(orderDetails.requested_delivery_date)}
                      </p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Retailer Contact Information */}
              {orderDetails?.retailer_info && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <User className="h-5 w-5 text-green-600" />
                    <h3 className="font-medium text-green-900">Retailer Contact</h3>
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-green-800">
                    {orderDetails.retailer_info.name && (
                      <p className="font-medium">{orderDetails.retailer_info.name}</p>
                    )}
                    {orderDetails.retailer_info.contact_person && (
                      <p>Contact: {orderDetails.retailer_info.contact_person}</p>
                    )}
                    {orderDetails.retailer_info.email && (
                      <p>Email: {orderDetails.retailer_info.email}</p>
                    )}
                    {orderDetails.retailer_info.phone && (
                      <p>Phone: {orderDetails.retailer_info.phone}</p>
                    )}
                    {orderDetails.retailer_info.address && (
                      <div className="mt-2">
                        <p className="font-medium">Address:</p>
                        {orderDetails.retailer_info.address.street && (
                          <p className="ml-2">{orderDetails.retailer_info.address.street}</p>
                        )}
                        {(orderDetails.retailer_info.address.city || orderDetails.retailer_info.address.state || orderDetails.retailer_info.address.zip_code) && (
                          <p className="ml-2">
                            {orderDetails.retailer_info.address.city && `${orderDetails.retailer_info.address.city}, `}
                            {orderDetails.retailer_info.address.state && `${orderDetails.retailer_info.address.state} `}
                            {orderDetails.retailer_info.address.zip_code}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-gray-500" />
                  <h3 className="font-medium text-gray-900">Timeline</h3>
                </div>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  <p>Created: {formatDateTime(orderDetails?.created_at)}</p>
                  <p>Updated: {formatDateTime(orderDetails?.updated_at)}</p>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => processOrderMutation.mutate()}
                disabled={processOrderMutation.isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                <span>{processOrderMutation.isLoading ? 'Processing...' : 'Process Order'}</span>
              </button>
              
              <button
                onClick={() => reprocessOrderMutation.mutate()}
                disabled={reprocessOrderMutation.isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" />
                <span>{reprocessOrderMutation.isLoading ? 'Reprocessing...' : 'Reprocess'}</span>
              </button>
              
              <button
                onClick={() => processWithAIMutation.mutate()}
                disabled={processWithAIMutation.isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                <Zap className="h-4 w-4" />
                <span>{processWithAIMutation.isLoading ? 'AI Processing...' : 'Process with AI'}</span>
              </button>
            </div>

            {/* Validation Results */}
            {orderDetails?.validation_errors && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="font-medium text-red-800 mb-2">Validation Issues</h3>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {orderDetails.validation_errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Processing Tab */}
        {activeTab === 'processing' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Processing Status */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Status</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Current Status</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(orderDetails?.status)}`}>
                      {orderDetails?.status}
                    </span>
                  </div>
                  
                  {orderDetails?.processing_notes && (
                    <div>
                      <span className="text-sm text-gray-600">Processing Notes</span>
                      <p className="mt-1 text-sm text-gray-900">{orderDetails.processing_notes}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Missing Information */}
              {orderDetails?.missing_fields && orderDetails.missing_fields.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-orange-800 mb-4">Missing Information</h3>
                  <ul className="space-y-2">
                    {orderDetails.missing_fields.map((field, index) => (
                      <li key={index} className="flex items-center space-x-2 text-sm text-orange-700">
                        <AlertCircle className="h-4 w-4" />
                        <span>{field}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Processing Actions */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <button
                  onClick={() => processOrderMutation.mutate()}
                  className="flex flex-col items-center p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Play className="h-8 w-8 text-blue-500 mb-2" />
                  <span className="text-sm font-medium">Process</span>
                </button>
                
                <button
                  onClick={() => reprocessOrderMutation.mutate()}
                  className="flex flex-col items-center p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <RotateCcw className="h-8 w-8 text-orange-500 mb-2" />
                  <span className="text-sm font-medium">Reprocess</span>
                </button>
                
                <button
                  onClick={() => setActiveTab('ai-agent')}
                  className="flex flex-col items-center p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Bot className="h-8 w-8 text-purple-500 mb-2" />
                  <span className="text-sm font-medium">AI Process</span>
                </button>
                
                <button
                  onClick={() => window.open(`/api/orders/${orderId}/download`, '_blank')}
                  className="flex flex-col items-center p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Download className="h-8 w-8 text-green-500 mb-2" />
                  <span className="text-sm font-medium">Download</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* AI Agent Tab */}
        {activeTab === 'ai-agent' && (
          <div className="space-y-6">
            {/* AI Agent Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">AI Agent Threads</h3>
                <p className="text-sm text-gray-600">Manage AI-powered order processing</p>
              </div>
              <button
                onClick={() => setShowCreateThread(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Bot className="h-4 w-4" />
                <span>New AI Thread</span>
              </button>
            </div>

            {/* Create Thread Modal */}
            {showCreateThread && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">Create New AI Thread</h4>
                <textarea
                  value={newThreadMessage}
                  onChange={(e) => setNewThreadMessage(e.target.value)}
                  placeholder="Enter instructions for the AI agent..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
                  rows={4}
                />
                <div className="mt-4 flex items-center space-x-3">
                  <button
                    onClick={handleCreateThread}
                    disabled={createAIThreadMutation.isLoading}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    {createAIThreadMutation.isLoading ? 'Creating...' : 'Create & Start'}
                  </button>
                  <button
                    onClick={() => setShowCreateThread(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* AI Threads List */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Active Threads</h4>
                {threadsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="h-6 w-6 animate-spin text-purple-500" />
                  </div>
                ) : aiThreads?.threads?.length > 0 ? (
                  <div className="space-y-3">
                    {aiThreads.data.threads.map((thread) => (
                      <div
                        key={thread.thread_id}
                        onClick={() => setSelectedThread(thread.thread_id)}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          selectedThread === thread.thread_id
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getThreadStatusIcon(thread.status)}
                            <span className="font-medium text-sm">{thread.status}</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatDateTime(thread.created_at)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Tools used: {thread.tools_used.join(', ') || 'None'}
                        </p>
                        {thread.status === 'RUNNING' && (
                          <div className="mt-2 flex items-center space-x-2 text-xs text-blue-600">
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            <span>Processing...</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No AI threads yet. Create one to get started.</p>
                  </div>
                )}
              </div>

              {/* Thread Details */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Thread Details</h4>
                {selectedThread && threadDetails ? (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Thread: {selectedThread.slice(-8)}</span>
                      <button
                        onClick={() => runAIAgentMutation.mutate(selectedThread)}
                        disabled={runAIAgentMutation.isLoading || threadDetails.data.status === 'RUNNING'}
                        className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:opacity-50"
                      >
                        {runAIAgentMutation.isLoading ? 'Running...' : 'Run Agent'}
                      </button>
                    </div>
                    
                    {threadDetails.data.messages && threadDetails.data.messages.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-sm font-medium text-gray-700">Messages:</span>
                        <div className="max-h-64 overflow-y-auto space-y-2">
                          {threadDetails.data.messages.map((message, index) => (
                            <div key={index} className="bg-white p-3 rounded border">
                              <div className="flex items-center space-x-2 mb-1">
                                <MessageSquare className="h-4 w-4" />
                                <span className="text-xs text-gray-500">{message.role}</span>
                              </div>
                              <p className="text-sm">{message.content || JSON.stringify(message)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-500">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>Select a thread to view details</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tracking Tab */}
        {activeTab === 'tracking' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Order Tracking Timeline</h3>
              <button
                onClick={() => queryClient.invalidateQueries(['order-tracking', orderId])}
                className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh</span>
              </button>
            </div>

            {/* Tracking Timeline */}
            {(() => {
              // Handle the actual API response structure 
              const trackingResponse = orderTracking?.data || orderTracking;
              
              // Extract tracking entries from the response
              let trackingEntries = [];
              
              if (Array.isArray(trackingResponse)) {
                trackingEntries = trackingResponse;
              } else if (trackingResponse && Array.isArray(trackingResponse.tracking_entries)) {
                trackingEntries = trackingResponse.tracking_entries;
              } else if (trackingResponse && typeof trackingResponse === 'object') {
                // Handle case where we get a single tracking object
                trackingEntries = [trackingResponse];
              }
              
              // Filter out invalid entries and sort by timestamp descending (newest first)
              const sortedEntries = trackingEntries
                .filter(entry => entry && (entry.id || entry.created_at))
                .sort((a, b) => 
                  new Date(b.created_at || b.timestamp || 0) - new Date(a.created_at || a.timestamp || 0)
                );

              const getEventIcon = (status) => {
                const iconMap = {
                  'UPLOADED': Upload,
                  'PROCESSING': Settings,
                  'ORDER_PROCESSING_COMPLETED': CheckCircle,
                  'VALIDATION_FAILED': XCircle,
                  'VALIDATION_ERRORS': XCircle,
                  'MISSING_INFO': AlertCircle,
                  'EMAIL_GENERATION_COMPLETED': Mail,
                  'EMAIL_GENERATION_STARTED': Mail,
                  'BUSINESS_RULE_VIOLATIONS': AlertCircle,
                  'CATALOG_VALIDATION': Settings,
                  'DATA_QUALITY_CHECKS': Settings,
                  'FILE_PARSING_STARTED': FileText,
                  'FILE_PARSING_COMPLETED': CheckCircle,
                  'CSV_EXTRACTION_COMPLETED': CheckCircle,
                  'CSV_FIELD_MAPPING': Settings,
                  'ORDER_VALIDATION_STARTED': Settings,
                  'ORDER_VALIDATION_FAILED': XCircle,
                  'REQUIRED_FIELDS_VALIDATION': Settings,
                  'DATA_TYPE_VALIDATION': Settings,
                  'BUSINESS_RULE_VALIDATION': Settings,
                  'AI_PROCESSING': Bot,
                  'STATUS_CHANGE': Activity,
                  'ERROR': AlertCircle,
                  'WARNING': AlertCircle,
                  'INFO': Activity,
                  'SUCCESS': CheckCircle,
                  'COMPLETED': CheckCircle,
                  'FAILED': XCircle,
                };
                return iconMap[status] || Activity;
              };

              const getEventColor = (status) => {
                const colorMap = {
                  'UPLOADED': 'text-blue-500 bg-blue-50',
                  'PROCESSING': 'text-yellow-500 bg-yellow-50',
                  'ORDER_PROCESSING_COMPLETED': 'text-green-500 bg-green-50',
                  'VALIDATION_FAILED': 'text-red-500 bg-red-50',
                  'VALIDATION_ERRORS': 'text-red-500 bg-red-50',
                  'MISSING_INFO': 'text-orange-500 bg-orange-50',
                  'EMAIL_GENERATION_COMPLETED': 'text-purple-500 bg-purple-50',
                  'EMAIL_GENERATION_STARTED': 'text-purple-500 bg-purple-50',
                  'BUSINESS_RULE_VIOLATIONS': 'text-red-500 bg-red-50',
                  'CATALOG_VALIDATION': 'text-blue-500 bg-blue-50',
                  'DATA_QUALITY_CHECKS': 'text-blue-500 bg-blue-50',
                  'FILE_PARSING_STARTED': 'text-blue-500 bg-blue-50',
                  'FILE_PARSING_COMPLETED': 'text-green-500 bg-green-50',
                  'CSV_EXTRACTION_COMPLETED': 'text-green-500 bg-green-50',
                  'CSV_FIELD_MAPPING': 'text-blue-500 bg-blue-50',
                  'ORDER_VALIDATION_STARTED': 'text-blue-500 bg-blue-50',
                  'ORDER_VALIDATION_FAILED': 'text-red-500 bg-red-50',
                  'REQUIRED_FIELDS_VALIDATION': 'text-yellow-500 bg-yellow-50',
                  'DATA_TYPE_VALIDATION': 'text-yellow-500 bg-yellow-50',
                  'BUSINESS_RULE_VALIDATION': 'text-yellow-500 bg-yellow-50',
                  'AI_PROCESSING': 'text-indigo-500 bg-indigo-50',
                  'STATUS_CHANGE': 'text-blue-500 bg-blue-50',
                  'ERROR': 'text-red-500 bg-red-50',
                  'WARNING': 'text-orange-500 bg-orange-50',
                  'INFO': 'text-gray-500 bg-gray-50',
                  'SUCCESS': 'text-green-500 bg-green-50',
                  'COMPLETED': 'text-green-500 bg-green-50',
                  'FAILED': 'text-red-500 bg-red-50',
                };
                return colorMap[status] || 'text-gray-500 bg-gray-50';
              };

              if (sortedEntries.length > 0) {
                return (
                  <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-8 top-6 bottom-0 w-0.5 bg-gray-200"></div>
                    
                    <div className="space-y-6">
                      {sortedEntries.map((entry, index) => {
                        const EventIcon = getEventIcon(entry.status);
                        const eventColors = getEventColor(entry.status);
                        
                        return (
                          <div key={entry.id || index} className="relative flex items-start">
                            {/* Timeline icon */}
                            <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 border-white shadow-md ${eventColors}`}>
                              <EventIcon className="h-4 w-4" />
                            </div>
                            
                            {/* Event content */}
                            <div className="ml-6 flex-1">
                              <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2 mb-2">
                                      <h4 className="font-semibold text-gray-900">
                                        {entry.status?.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase()) || 'Event'}
                                      </h4>
                                      {entry.status && (
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                          entry.status.includes('COMPLETED') || entry.status.includes('SUCCESS') ? 'bg-green-100 text-green-800' :
                                          entry.status.includes('FAILED') || entry.status.includes('ERROR') ? 'bg-red-100 text-red-800' :
                                          entry.status.includes('PROCESSING') || entry.status.includes('STARTED') ? 'bg-yellow-100 text-yellow-800' :
                                          entry.status.includes('MISSING') || entry.status.includes('VALIDATION') ? 'bg-orange-100 text-orange-800' :
                                          'bg-gray-100 text-gray-800'
                                        }`}>
                                          {entry.status}
                                        </span>
                                      )}
                                    </div>
                                    
                                    <p className="text-gray-700 mb-2">
                                      {entry.message || entry.description || 'Processing step completed'}
                                    </p>
                                    
                                    {/* Additional details */}
                                    {entry.details && (
                                      <div className="mt-3 p-3 bg-gray-50 rounded-md">
                                        <details className="group">
                                          <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                                            View Details
                                          </summary>
                                          <div className="mt-2 text-xs text-gray-600">
                                            <pre className="whitespace-pre-wrap overflow-x-auto">
                                              {typeof entry.details === 'string' ? entry.details : JSON.stringify(entry.details, null, 2)}
                                            </pre>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                    
                                    {/* Metadata */}
                                    <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                                      <span className="flex items-center space-x-1">
                                        <Clock className="h-3 w-3" />
                                        <span>{formatDateTime(entry.created_at || entry.timestamp)}</span>
                                      </span>
                                      {entry.id && (
                                        <span className="flex items-center space-x-1">
                                          <span>•</span>
                                          <span>ID: {entry.id.slice(0, 8)}...</span>
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              } else {
                return (
                  <div className="text-center py-12">
                    <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <Activity className="h-12 w-12 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No tracking events yet</h3>
                    <p className="text-gray-500 mb-4">
                      Tracking events will appear here as your order progresses through the system.
                    </p>
                    {/* Debug info */}
                    <details className="text-left">
                      <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                        Debug: View Raw Response
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto text-left">
                        {JSON.stringify(orderTracking, null, 2)}
                      </pre>
                    </details>
                  </div>
                );
              }
            })()}
          </div>
        )}

        {/* SKU Items Tab */}
        {activeTab === 'sku-items' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">SKU Items Details</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => queryClient.invalidateQueries(['order-sku-items', orderId])}
                  className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            {/* SKU Items Table */}
            {(() => {
              const skuItems = orderSKUItems?.data || orderSKUItems || [];
              
              if (!skuItems || skuItems.length === 0) {
                return (
                  <div className="text-center py-12">
                    <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <Package className="h-12 w-12 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No SKU items found</h3>
                    <p className="text-gray-500 mb-4">
                      SKU items will appear here once the order has been processed and parsed.
                    </p>
                  </div>
                );
              }

              return (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="mb-4 text-sm text-gray-600">
                      Found {skuItems.length} SKU item{skuItems.length !== 1 ? 's' : ''} in this order
                      {orderDetails?.total_sku_count && orderDetails.total_sku_count !== skuItems.length && (
                        <span className="ml-2 text-blue-600">
                          (Order summary shows {orderDetails.total_sku_count} total SKUs)
                        </span>
                      )}
                    </div>
                    
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              SKU Code
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Product Name
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Category/Brand
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Quantity
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Pricing
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Physical Details
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Processing Remarks
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {skuItems.map((item, index) => (
                            <tr key={item.id || index} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="flex-shrink-0 h-8 w-8">
                                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                      <Package className="h-4 w-4 text-blue-600" />
                                    </div>
                                  </div>
                                  <div className="ml-4">
                                    <div className="text-sm font-medium text-gray-900">
                                      {item.sku_code || 'N/A'}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-gray-900">
                                  {item.product_name || 'N/A'}
                                </div>
                                {item.product_attributes && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    <details>
                                      <summary className="cursor-pointer">Attributes</summary>
                                      <pre className="mt-1 text-xs bg-gray-50 p-2 rounded">
                                        {JSON.stringify(item.product_attributes, null, 2)}
                                      </pre>
                                    </details>
                                  </div>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {item.category && (
                                    <div className="text-sm text-gray-900">{item.category}</div>
                                  )}
                                  {item.brand && (
                                    <div className="text-xs text-gray-500">{item.brand}</div>
                                  )}
                                  {!item.category && !item.brand && 'N/A'}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {item.quantity_ordered || 0} {item.unit_of_measure || 'units'}
                                </div>
                                {item.fragile && (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mt-1">
                                    Fragile
                                  </span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {item.unit_price && (
                                    <div>Unit: ${parseFloat(item.unit_price).toFixed(2)}</div>
                                  )}
                                  {item.total_price && (
                                    <div className="font-medium">Total: ${parseFloat(item.total_price).toFixed(2)}</div>
                                  )}
                                  {!item.unit_price && !item.total_price && 'No pricing'}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {item.weight_kg && (
                                    <div>Weight: {item.weight_kg} kg</div>
                                  )}
                                  {item.volume_m3 && (
                                    <div>Volume: {item.volume_m3} m³</div>
                                  )}
                                  {item.temperature_requirement && (
                                    <div className="text-xs text-blue-600">
                                      Temp: {item.temperature_requirement}
                                    </div>
                                  )}
                                  {!item.weight_kg && !item.volume_m3 && !item.temperature_requirement && 'N/A'}
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-gray-900">
                                  {item.processing_remarks ? (
                                    <div className="max-w-xs">
                                      <div className="text-sm bg-yellow-50 border border-yellow-200 rounded p-2">
                                        {item.processing_remarks}
                                      </div>
                                    </div>
                                  ) : (
                                    <span className="text-gray-400 italic">No remarks</span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Summary Stats - Using aggregated data from orders table */}
                    <div className="mt-6 border-t border-gray-200 pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        <div className="bg-blue-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-blue-600">Total SKUs</div>
                          <div className="text-2xl font-bold text-blue-900">
                            {orderDetails?.total_sku_count || skuItems.length}
                          </div>
                          <div className="text-xs text-blue-500 mt-1">Unique items</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-green-600">Total Quantity</div>
                          <div className="text-2xl font-bold text-green-900">
                            {orderDetails?.total_quantity || skuItems.reduce((sum, item) => sum + (parseInt(item.quantity_ordered) || 0), 0)}
                          </div>
                          <div className="text-xs text-green-500 mt-1">Units ordered</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-purple-600">Total Weight</div>
                          <div className="text-2xl font-bold text-purple-900">
                            {orderDetails?.total_weight_kg ? `${parseFloat(orderDetails.total_weight_kg).toFixed(2)} kg` : 'N/A'}
                          </div>
                          <div className="text-xs text-purple-500 mt-1">Kilograms</div>
                        </div>
                        <div className="bg-indigo-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-indigo-600">Subtotal</div>
                          <div className="text-2xl font-bold text-indigo-900">
                            ${orderDetails?.subtotal ? parseFloat(orderDetails.subtotal).toFixed(2) : '0.00'}
                          </div>
                          <div className="text-xs text-indigo-500 mt-1">Order value</div>
                        </div>
                        <div className="bg-orange-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-orange-600">Items with Remarks</div>
                          <div className="text-2xl font-bold text-orange-900">
                            {skuItems.filter(item => item.processing_remarks).length}
                          </div>
                          <div className="text-xs text-orange-500 mt-1">Need attention</div>
                        </div>
                      </div>

                      {/* Additional aggregated details from orders table */}
                      {orderDetails?.total_volume_m3 && (
                        <div className="mt-4 bg-gray-50 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm font-medium text-gray-600">Total Volume</div>
                              <div className="text-lg font-bold text-gray-900">
                                {parseFloat(orderDetails.total_volume_m3).toFixed(3)} m³
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-medium text-gray-600">Tax Amount</div>
                              <div className="text-lg font-bold text-gray-900">
                                ${orderDetails.tax ? parseFloat(orderDetails.tax).toFixed(2) : '0.00'}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-medium text-gray-600">Total Amount</div>
                              <div className="text-lg font-bold text-gray-900">
                                ${orderDetails.total ? parseFloat(orderDetails.total).toFixed(2) : '0.00'}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Emails Tab */}
        {activeTab === 'emails' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Email Communications</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => queryClient.invalidateQueries(['email-communications', orderId])}
                  className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            {/* Email Communications Timeline */}
            {(() => {
              // Handle the email communications response structure
              const emailResponse = emailCommunications?.data || emailCommunications;
              
              // Extract email entries from the response
              let emailEntries = [];
              
              if (Array.isArray(emailResponse)) {
                emailEntries = emailResponse;
              } else if (emailResponse && Array.isArray(emailResponse.emails)) {
                emailEntries = emailResponse.emails;
              } else if (emailResponse && Array.isArray(emailResponse.communications)) {
                emailEntries = emailResponse.communications;
              } else if (emailResponse && typeof emailResponse === 'object') {
                // Handle case where we get a single email object
                emailEntries = [emailResponse];
              }
              
              // Filter out invalid entries and sort by timestamp descending (newest first)
              const sortedEntries = emailEntries
                .filter(entry => entry && (entry.id || entry.created_at || entry.timestamp))
                .sort((a, b) => 
                  new Date(b.sent_at || b.created_at || b.timestamp || 0) - new Date(a.sent_at || a.created_at || a.timestamp || 0)
                );

              const getEmailStatusColor = (status) => {
                const colorMap = {
                  'SENT': 'text-green-500 bg-green-50',
                  'DELIVERED': 'text-green-600 bg-green-100',
                  'PENDING': 'text-yellow-500 bg-yellow-50',
                  'FAILED': 'text-red-500 bg-red-50',
                  'DRAFT': 'text-gray-500 bg-gray-50',
                  'BOUNCED': 'text-red-600 bg-red-100',
                  'OPENED': 'text-blue-500 bg-blue-50',
                  'CLICKED': 'text-purple-500 bg-purple-50',
                };
                return colorMap[status] || 'text-gray-500 bg-gray-50';
              };

              const getEmailTypeIcon = (type) => {
                const iconMap = {
                  'ORDER_CONFIRMATION': CheckCircle,
                  'SHIPMENT_NOTIFICATION': Package,
                  'DELIVERY_UPDATE': Activity,
                  'VALIDATION_ERROR': AlertCircle,
                  'MISSING_INFO_REQUEST': AlertCircle,
                  'MANUFACTURER_NOTIFICATION': Bot,
                  'SYSTEM_ALERT': Bell,
                  'MANUAL': Mail,
                  'AUTOMATED': Bot,
                };
                return iconMap[type] || Mail;
              };

              const handleFileUpload = (file, emailId, errorType) => {
                if (!file) {
                  toast.error('Please select a file to upload');
                  return;
                }

                // Validate file type
                const allowedTypes = ['.csv', '.xlsx', '.xls'];
                const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
                
                if (!allowedTypes.includes(fileExtension)) {
                  toast.error('Please upload a valid file format (CSV, Excel .xlsx, .xls)');
                  return;
                }

                // Validate file size (max 10MB)
                if (file.size > 10 * 1024 * 1024) {
                  toast.error('File size must be less than 10MB');
                  return;
                }

                uploadCorrectionMutation.mutate({ file, emailId, errorType });
              };

              const renderErrorActions = (email) => {
                const isErrorEmail = email.email_type === 'VALIDATION_ERROR' || 
                                   email.email_type === 'MISSING_INFO_REQUEST' ||
                                   email.subject?.toLowerCase().includes('error') ||
                                   email.subject?.toLowerCase().includes('validation') ||
                                   email.subject?.toLowerCase().includes('failed');

                if (!isErrorEmail) return null;

                return (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h5 className="font-medium text-red-800 mb-2">Action Required</h5>
                        <p className="text-sm text-red-700 mb-3">
                          This email contains validation errors that need to be addressed. 
                          Please review the error details above and upload a corrected file to resolve these issues.
                        </p>
                        
                        {/* Error summary */}
                        {(email.errors || email.validation_errors) && (
                          <div className="mb-3 p-3 bg-red-100 rounded-md">
                            <h6 className="text-sm font-medium text-red-800 mb-1">
                              {email.errors?.length || email.validation_errors?.length || 0} error(s) found:
                            </h6>
                            <ul className="text-xs text-red-700 list-disc list-inside">
                              {(email.errors || email.validation_errors || []).slice(0, 3).map((error, idx) => (
                                <li key={idx}>{error}</li>
                              ))}
                              {(email.errors?.length || email.validation_errors?.length || 0) > 3 && (
                                <li>... and {(email.errors?.length || email.validation_errors?.length) - 3} more</li>
                              )}
                            </ul>
                          </div>
                        )}
                        
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                          <label className={`cursor-pointer ${uploadCorrectionMutation.isLoading ? 'opacity-50 pointer-events-none' : ''}`}>
                            <input
                              type="file"
                              accept=".csv,.xlsx,.xls"
                              className="hidden"
                              disabled={uploadCorrectionMutation.isLoading}
                              onChange={(e) => {
                                const file = e.target.files[0];
                                if (file) {
                                  handleFileUpload(file, email.id, email.email_type);
                                }
                                // Reset the input
                                e.target.value = '';
                              }}
                            />
                            <span className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                              {uploadCorrectionMutation.isLoading ? (
                                <RefreshCw className="h-4 w-4 animate-spin" />
                              ) : (
                                <Upload className="h-4 w-4" />
                              )}
                              <span>
                                {uploadCorrectionMutation.isLoading ? 'Uploading...' : 'Upload Corrected File'}
                              </span>
                            </span>
                          </label>
                          
                          <button
                            onClick={() => {
                              // Download original file for reference
                              window.open(`/api/orders/${orderId}/download-original`, '_blank');
                            }}
                            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                          >
                            <Download className="h-4 w-4" />
                            <span>Download Original</span>
                          </button>
                          
                          <button
                            onClick={() => {
                              // Download sample template
                              const link = document.createElement('a');
                              link.href = '/uploads/sample_order.csv';
                              link.download = 'sample_order_template.csv';
                              link.click();
                            }}
                            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            <FileText className="h-4 w-4" />
                            <span>Download Template</span>
                          </button>
                        </div>
                        
                        <div className="mt-3 text-xs text-red-600">
                          <p>📁 <strong>Supported formats:</strong> CSV, Excel (.xlsx, .xls)</p>
                          <p>📏 <strong>Maximum file size:</strong> 10MB</p>
                          <p>💡 <strong>Tip:</strong> Use the template to ensure correct formatting</p>
                        </div>

                        {/* Upload progress or success message */}
                        {uploadCorrectionMutation.isLoading && (
                          <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
                            <p className="text-sm text-blue-700 flex items-center">
                              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                              Uploading and processing your corrected file...
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              };

              if (sortedEntries.length > 0) {
                return (
                  <div className="space-y-4">
                    {sortedEntries.map((email, index) => {
                      const EmailIcon = getEmailTypeIcon(email.email_type || email.type);
                      const statusColors = getEmailStatusColor(email.status);
                      
                      return (
                        <div key={email.id || index} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                          <div className="p-6">
                            {/* Email Header */}
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex items-start space-x-3">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${statusColors}`}>
                                  <EmailIcon className="h-5 w-5" />
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <h4 className="font-semibold text-gray-900">
                                      {email.subject || email.email_type?.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase()) || 'Email Communication'}
                                    </h4>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                      email.status === 'SENT' || email.status === 'DELIVERED' ? 'bg-green-100 text-green-800' :
                                      email.status === 'FAILED' || email.status === 'BOUNCED' ? 'bg-red-100 text-red-800' :
                                      email.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                                      email.status === 'DRAFT' ? 'bg-gray-100 text-gray-800' :
                                      'bg-blue-100 text-blue-800'
                                    }`}>
                                      {email.status || 'UNKNOWN'}
                                    </span>
                                  </div>
                                  
                                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                                    <span className="flex items-center space-x-1">
                                      <span>To:</span>
                                      <span className="font-medium">{email.recipient_email || email.to_email || 'N/A'}</span>
                                    </span>
                                    {email.sent_at && (
                                      <span className="flex items-center space-x-1">
                                        <Clock className="h-3 w-3" />
                                        <span>{formatDateTime(email.sent_at)}</span>
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                              
                              {/* Email Actions */}
                              <div className="flex items-center space-x-2">
                                {email.email_type && (
                                  <span className={`px-2 py-1 text-xs rounded-md ${
                                    email.email_type === 'VALIDATION_ERROR' ? 'bg-red-50 text-red-700' :
                                    email.email_type === 'MISSING_INFO_REQUEST' ? 'bg-orange-50 text-orange-700' :
                                    'bg-blue-50 text-blue-700'
                                  }`}>
                                    {email.email_type.replace(/_/g, ' ')}
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Error Details Section */}
                            {(email.errors || email.validation_errors || email.error_details) && (
                              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                                <h5 className="font-medium text-red-800 mb-2 flex items-center">
                                  <AlertCircle className="h-4 w-4 mr-2" />
                                  Error Details
                                </h5>
                                <div className="space-y-2">
                                  {/* Display validation errors */}
                                  {email.errors && Array.isArray(email.errors) && (
                                    <div>
                                      <h6 className="text-sm font-medium text-red-700 mb-1">Validation Errors:</h6>
                                      <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                                        {email.errors.map((error, idx) => (
                                          <li key={idx}>{error}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Display missing fields */}
                                  {email.missing_fields && Array.isArray(email.missing_fields) && (
                                    <div>
                                      <h6 className="text-sm font-medium text-red-700 mb-1">Missing Fields:</h6>
                                      <div className="flex flex-wrap gap-1">
                                        {email.missing_fields.map((field, idx) => (
                                          <span key={idx} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">
                                            {field}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {/* Display error details */}
                                  {email.error_details && (
                                    <div>
                                      <h6 className="text-sm font-medium text-red-700 mb-1">Error Details:</h6>
                                      <p className="text-sm text-red-600">{email.error_details}</p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Email Preview */}
                            {email.content && (
                              <div className="mb-4">
                                <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                                  <details className="group">
                                    <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center justify-between">
                                      <span>Email Content Preview</span>
                                      <span className="text-xs text-gray-500 group-open:hidden">Click to expand</span>
                                    </summary>
                                    <div className="mt-3 text-sm text-gray-700">
                                      {email.content.length > 300 ? (
                                        <div>
                                          <div className="whitespace-pre-wrap">
                                            {email.content.substring(0, 300)}...
                                          </div>
                                          <details className="mt-2">
                                            <summary className="cursor-pointer text-blue-600 hover:text-blue-800 text-xs">
                                              Show full content
                                            </summary>
                                            <div className="mt-2 whitespace-pre-wrap text-xs">
                                              {email.content}
                                            </div>
                                          </details>
                                        </div>
                                      ) : (
                                        <div className="whitespace-pre-wrap">{email.content}</div>
                                      )}
                                    </div>
                                  </details>
                                </div>
                              </div>
                            )}

                            {/* Error Actions - Upload Correction */}
                            {renderErrorActions(email)}

                            {/* Email Metadata */}
                            <div className="border-t border-gray-100 pt-4">
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500">
                                {email.message_id && (
                                  <div>
                                    <span className="font-medium">Message ID:</span>
                                    <div className="truncate">{email.message_id.slice(0, 20)}...</div>
                                  </div>
                                )}
                                {email.email_provider && (
                                  <div>
                                    <span className="font-medium">Provider:</span>
                                    <div>{email.email_provider}</div>
                                  </div>
                                )}
                                {email.delivery_attempts && (
                                  <div>
                                    <span className="font-medium">Attempts:</span>
                                    <div>{email.delivery_attempts}</div>
                                  </div>
                                )}
                                {email.last_error && (
                                  <div>
                                    <span className="font-medium text-red-600">Error:</span>
                                    <div className="text-red-600 truncate">{email.last_error}</div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Additional Details */}
                            {email.metadata && Object.keys(email.metadata).length > 0 && (
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <details className="group">
                                  <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                                    Technical Details
                                  </summary>
                                  <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
                                    <pre className="whitespace-pre-wrap overflow-x-auto">
                                      {JSON.stringify(email.metadata, null, 2)}
                                    </pre>
                                  </div>
                                </details>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              } else {
                return (
                  <div className="text-center py-12">
                    <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <Mail className="h-12 w-12 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No email communications yet</h3>
                    <p className="text-gray-500 mb-4">
                      Email communications will appear here when the system sends notifications about this order.
                    </p>
                    
                    {/* Email Statistics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-md mx-auto mt-6">
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="text-2xl font-bold text-green-600">0</div>
                        <div className="text-sm text-gray-600">Sent</div>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="text-2xl font-bold text-yellow-600">0</div>
                        <div className="text-sm text-gray-600">Pending</div>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="text-2xl font-bold text-red-600">0</div>
                        <div className="text-sm text-gray-600">Failed</div>
                      </div>
                    </div>
                    
                    {/* Debug info */}
                    <details className="text-left mt-6">
                      <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                        Debug: View Raw Response
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto text-left">
                        {JSON.stringify(emailCommunications, null, 2)}
                      </pre>
                    </details>
                  </div>
                );
              }
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderProcessingScreen;
