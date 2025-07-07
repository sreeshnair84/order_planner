import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import Layout from '../components/common/Layout';
import { orderService } from '../services/orderService';
import { 
  Package, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Eye, 
  Filter,
  Search
} from 'lucide-react';

const TrackingPage = () => {
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);

  const { data: ordersData, isLoading } = useQuery(
    ['orders', statusFilter],
    () => orderService.getOrders({ status: statusFilter || undefined }),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: trackingData, isLoading: trackingLoading } = useQuery(
    ['tracking', selectedOrder],
    () => orderService.getOrderTracking(selectedOrder),
    {
      enabled: !!selectedOrder,
    }
  );

  const orders = ordersData?.orders || [];
  const filteredOrders = orders.filter(order =>
    order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.original_filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusIcon = (status) => {
    switch (status) {
      case 'UPLOADED':
        return <Package className="h-5 w-5 text-blue-600" />;
      case 'PROCESSING':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case 'PENDING_INFO':
        return <AlertCircle className="h-5 w-5 text-orange-600" />;
      case 'INFO_RECEIVED':
        return <CheckCircle className="h-5 w-5 text-blue-600" />;
      case 'VALIDATED':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'TRIP_QUEUED':
        return <Clock className="h-5 w-5 text-purple-600" />;
      case 'TRIP_PLANNED':
        return <CheckCircle className="h-5 w-5 text-purple-600" />;
      case 'SUBMITTED':
        return <Package className="h-5 w-5 text-indigo-600" />;
      case 'CONFIRMED':
        return <CheckCircle className="h-5 w-5 text-indigo-600" />;
      case 'IN_TRANSIT':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'DELIVERED':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'CANCELLED':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'REJECTED':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'UPLOADED':
        return 'status-badge status-uploaded';
      case 'PROCESSING':
        return 'status-badge status-processing';
      case 'PENDING_INFO':
        return 'status-badge status-pending-info';
      case 'INFO_RECEIVED':
        return 'status-badge bg-blue-100 text-blue-800';
      case 'VALIDATED':
        return 'status-badge status-validated';
      case 'TRIP_QUEUED':
        return 'status-badge bg-purple-100 text-purple-800';
      case 'TRIP_PLANNED':
        return 'status-badge bg-purple-100 text-purple-800';
      case 'SUBMITTED':
        return 'status-badge status-submitted';
      case 'CONFIRMED':
        return 'status-badge bg-indigo-100 text-indigo-800';
      case 'IN_TRANSIT':
        return 'status-badge bg-blue-100 text-blue-800';
      case 'DELIVERED':
        return 'status-badge status-delivered';
      case 'CANCELLED':
        return 'status-badge status-cancelled';
      case 'REJECTED':
        return 'status-badge status-rejected';
      default:
        return 'status-badge bg-gray-100 text-gray-800';
    }
  };

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'UPLOADED', label: 'Uploaded' },
    { value: 'PROCESSING', label: 'Processing' },
    { value: 'PENDING_INFO', label: 'Pending Info' },
    { value: 'INFO_RECEIVED', label: 'Info Received' },
    { value: 'VALIDATED', label: 'Validated' },
    { value: 'TRIP_QUEUED', label: 'Trip Queued' },
    { value: 'TRIP_PLANNED', label: 'Trip Planned' },
    { value: 'SUBMITTED', label: 'Submitted' },
    { value: 'CONFIRMED', label: 'Confirmed' },
    { value: 'IN_TRANSIT', label: 'In Transit' },
    { value: 'DELIVERED', label: 'Delivered' },
    { value: 'CANCELLED', label: 'Cancelled' },
    { value: 'REJECTED', label: 'Rejected' },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Order Tracking</h1>
            <p className="mt-2 text-sm text-gray-700">
              Monitor the status and progress of all your orders.
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <Link
              to="/upload"
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              <Package className="h-4 w-4 mr-2" />
              Upload New Order
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search orders..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="sm:w-48">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Filter className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Orders List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading orders...</p>
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-8">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                {orders.length === 0 ? 'No orders found' : 'No orders match your filters'}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {orders.length === 0 
                  ? 'Get started by uploading your first order file.'
                  : 'Try adjusting your search or filter criteria.'
                }
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredOrders.map((order) => (
                <li key={order.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        {getStatusIcon(order.status)}
                      </div>
                      <div className="ml-4 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">
                            {order.order_number}
                          </p>
                          <div className="ml-2 flex-shrink-0">
                            <span className={getStatusBadgeClass(order.status)}>
                              {order.status}
                            </span>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500">
                          <p className="truncate">
                            File: {order.original_filename}
                          </p>
                          <span className="mx-2">•</span>
                          <p className="whitespace-nowrap">
                            {new Date(order.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedOrder(order.id)}
                        className="inline-flex items-center p-1 border border-transparent text-sm leading-4 font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Order Details Modal */}
        {selectedOrder && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
              
              <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Order Tracking Details
                    </h3>
                    <button
                      onClick={() => setSelectedOrder(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <span className="sr-only">Close</span>
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  {trackingLoading ? (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-500">Loading tracking details...</p>
                    </div>
                  ) : trackingData ? (
                    <div className="space-y-4">
                      <div className="border-b pb-4">
                        <h4 className="font-medium text-gray-900">
                          {trackingData.order_number}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Current Status: 
                          <span className={`ml-2 ${getStatusBadgeClass(trackingData.current_status)}`}>
                            {trackingData.current_status}
                          </span>
                        </p>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-gray-900 mb-3">Tracking Timeline</h5>
                        <div className="space-y-3">
                          {trackingData.tracking_entries.map((entry, index) => (
                            <div key={entry.id} className="flex items-start">
                              <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                              <div className="ml-3 flex-1">
                                <div className="flex items-center justify-between">
                                  <p className="text-sm font-medium text-gray-900">
                                    {entry.status}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    {new Date(entry.created_at).toLocaleString()}
                                  </p>
                                </div>
                                {entry.message && (
                                  <p className="text-sm text-gray-600 mt-1">
                                    {entry.message}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-center text-gray-500">
                      Failed to load tracking details.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default TrackingPage;
