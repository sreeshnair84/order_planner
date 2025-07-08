import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useQuery, useMutation } from 'react-query';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import Layout from '../components/common/Layout';
import OrderProcessingScreen from '../components/OrderProcessingScreen';
import { orderService } from '../services/orderService';
import { 
  Upload, 
  File, 
  X, 
  Package, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Eye, 
  Filter,
  Search,
  Play,
  Settings,
  FileText,
  Plus,
  Download
} from 'lucide-react';

const OrderCreationPage = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showProcessingScreen, setShowProcessingScreen] = useState(false);
  const [processingOrderId, setProcessingOrderId] = useState(null);
  const { register, handleSubmit, reset } = useForm();

  // Queries
  const { data: ordersData, isLoading, refetch } = useQuery(
    ['orders', statusFilter],
    () => orderService.getOrders({ status: statusFilter || undefined }),
    {
      refetchInterval: 30000,
    }
  );

  const { data: orderDetails } = useQuery(
    ['order-details', selectedOrder],
    () => orderService.getOrderDetails(selectedOrder),
    {
      enabled: !!selectedOrder,
    }
  );

  // Mutations
  const uploadMutation = useMutation(
    ({ file, metadata }) => orderService.uploadOrder(file, metadata),
    {
      onSuccess: (data) => {
        toast.success('Order uploaded successfully!');
        setSelectedFile(null);
        reset();
        refetch();
        setActiveTab('tracking');
      },
      onError: (error) => {
        toast.error(error.detail || 'Upload failed. Please try again.');
      },
    }
  );

  const processMutation = useMutation(
    (orderId) => orderService.processOrder(orderId),
    {
      onSuccess: () => {
        toast.success('Order processing started!');
        refetch();
      },
      onError: (error) => {
        toast.error(error.detail || 'Processing failed. Please try again.');
      },
    }
  );

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
      'text/plain': ['.txt', '.log'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
      }
    },
    onDropRejected: (rejectedFiles) => {
      const file = rejectedFiles[0];
      if (file.errors.some(e => e.code === 'file-too-large')) {
        toast.error('File is too large. Maximum size is 10MB.');
      } else if (file.errors.some(e => e.code === 'file-invalid-type')) {
        toast.error('Invalid file type. Please upload CSV, XML, or LOG files.');
      } else {
        toast.error('File upload failed. Please try again.');
      }
    }
  });

  const orders = ordersData?.orders || [];
  const filteredOrders = orders.filter(order =>
    order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.original_filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const onSubmit = (data) => {
    if (!selectedFile) {
      toast.error('Please select a file to upload.');
      return;
    }

    uploadMutation.mutate({ file: selectedFile, metadata: data });
  };

  const handleProcessOrder = (orderId) => {
    processMutation.mutate(orderId);
  };

  const handleViewOrder = (orderId) => {
    setProcessingOrderId(orderId);
    setShowProcessingScreen(true);
  };

  const handleCloseProcessingScreen = () => {
    setShowProcessingScreen(false);
    setProcessingOrderId(null);
    refetch(); // Refresh the orders list
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'UPLOADED':
        return <Package className="h-5 w-5 text-blue-600" />;
      case 'PROCESSING':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case 'PENDING_INFO':
        return <AlertCircle className="h-5 w-5 text-orange-600" />;
      case 'VALIDATED':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'DELIVERED':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'UPLOADED':
        return 'bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium';
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium';
      case 'PENDING_INFO':
        return 'bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium';
      case 'VALIDATED':
        return 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium';
      case 'DELIVERED':
        return 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium';
      default:
        return 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium';
    }
  };

  const tabs = [
    { id: 'upload', name: 'Upload Orders', icon: Upload },
    { id: 'tracking', name: 'Track Orders', icon: Package },
    { id: 'processing', name: 'Process Orders', icon: Settings },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Order Creation</h1>
            <p className="mt-2 text-sm text-gray-700">
              Upload, track, and process orders in one centralized location.
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'upload' && (
            <div className="space-y-6">
              {/* Upload Form */}
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Order File</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  {/* File Upload Area */}
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-300 hover:border-blue-400'
                    }`}
                  >
                    <input {...getInputProps()} />
                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    {selectedFile ? (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-gray-900">
                          Selected: {selectedFile.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedFile(null);
                          }}
                          className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <X className="h-3 w-3 mr-1" />
                          Remove
                        </button>
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">
                          Drag and drop your order file here, or click to select
                        </p>
                        <p className="text-xs text-gray-500">
                          Supports CSV, XML, and LOG files up to 10MB
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Metadata Fields */}
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Order Priority
                      </label>
                      <select
                        {...register('priority')}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      >
                        <option value="">Select priority</option>
                        <option value="LOW">Low</option>
                        <option value="NORMAL">Normal</option>
                        <option value="HIGH">High</option>
                        <option value="URGENT">Urgent</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Expected Delivery Date
                      </label>
                      <input
                        type="date"
                        {...register('expected_delivery_date')}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Special Instructions
                      </label>
                      <textarea
                        {...register('special_instructions')}
                        rows={3}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        placeholder="Any special handling instructions..."
                      />
                    </div>
                  </div>

                  {/* Submit Button */}
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!selectedFile || uploadMutation.isLoading}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {uploadMutation.isLoading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Upload className="h-4 w-4 mr-2" />
                      )}
                      Upload Order
                    </button>
                  </div>
                </form>
              </div>

              {/* Sample Files */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Sample Files</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                    <div className="flex items-center">
                      <File className="h-5 w-5 text-gray-400 mr-2" />
                      <span className="text-sm text-gray-700">sample_order.csv</span>
                    </div>
                    <button className="text-blue-600 hover:text-blue-500">
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tracking' && (
            <div className="space-y-6">
              {/* Filters */}
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search orders..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">All Statuses</option>
                      <option value="UPLOADED">Uploaded</option>
                      <option value="PROCESSING">Processing</option>
                      <option value="PENDING_INFO">Pending Info</option>
                      <option value="VALIDATED">Validated</option>
                      <option value="DELIVERED">Delivered</option>
                    </select>
                  </div>
                  <button
                    onClick={() => refetch()}
                    className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Refresh
                  </button>
                </div>
              </div>

              {/* Orders List */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Orders</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {isLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-500">Loading orders...</p>
                    </div>
                  ) : filteredOrders.length === 0 ? (
                    <div className="text-center py-8">
                      <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-sm text-gray-500">No orders found</p>
                    </div>
                  ) : (
                    filteredOrders.map((order) => (
                      <div key={order.id} className="px-6 py-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            {getStatusIcon(order.status)}
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {order.order_number}
                              </p>
                              <p className="text-sm text-gray-500">
                                {order.original_filename}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <span className={getStatusBadgeClass(order.status)}>
                              {order.status}
                            </span>
                            <button
                              onClick={() => setSelectedOrder(order.id)}
                              className="text-blue-600 hover:text-blue-500"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'processing' && (
            <div className="space-y-6">
              {/* Processing Actions */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Order Processing</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    onClick={() => toast.success('Bulk processing initiated')}
                    className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    <Play className="h-5 w-5 mr-2 text-green-600" />
                    Process All Pending
                  </button>
                  <button
                    onClick={() => toast.success('Validation started')}
                    className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    <CheckCircle className="h-5 w-5 mr-2 text-blue-600" />
                    Validate Orders
                  </button>
                  <button
                    onClick={() => toast.success('Export started')}
                    className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    <Download className="h-5 w-5 mr-2 text-purple-600" />
                    Export Report
                  </button>
                </div>
              </div>

              {/* Individual Order Processing */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Individual Order Processing</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {filteredOrders
                    .filter(order => ['UPLOADED', 'PROCESSING', 'PENDING_INFO','MISSING_INFO'].includes(order.status))
                    .map((order) => (
                      <div key={order.id} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            {getStatusIcon(order.status)}
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {order.order_number}
                              </p>
                              <p className="text-sm text-gray-500">
                                {order.original_filename}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={getStatusBadgeClass(order.status)}>
                              {order.status}
                            </span>
                            <button
                              onClick={() => handleViewOrder(order.id)}
                              className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                            >
                              <Eye className="h-3 w-3 mr-1" />
                              View
                            </button>
                            <button
                              onClick={() => handleProcessOrder(order.id)}
                              disabled={processMutation.isLoading}
                              className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                            >
                              <Play className="h-3 w-3 mr-1" />
                              Process
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Order Processing Screen Modal */}
      {showProcessingScreen && processingOrderId && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-7xl shadow-lg rounded-md bg-white">
            <OrderProcessingScreen 
              orderId={processingOrderId}
              onClose={handleCloseProcessingScreen}
            />
          </div>
        </div>
      )}
    </Layout>
  );
};

export default OrderCreationPage;
