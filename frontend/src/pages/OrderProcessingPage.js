import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import Layout from '../components/common/Layout';
import { orderService } from '../services/orderService';
import OrderProcessingMainMenu from '../components/order-processing/OrderProcessingMainMenu';
import {
  Package,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Mail,
  FileText,
  Settings,
  Eye,
  Play,
  Pause,
  MoreHorizontal
} from 'lucide-react';

const OrderProcessingPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [selectedOrder, setSelectedOrder] = useState(orderId || null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showProcessingMenu, setShowProcessingMenu] = useState(false);

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

  const orders = ordersData?.orders || [];
  const filteredOrders = orders.filter(order =>
    order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.original_filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    if (orderId && orderId !== selectedOrder) {
      setSelectedOrder(orderId);
      setShowProcessingMenu(true);
    }
  }, [orderId, selectedOrder]);

  const handleOrderSelect = (order) => {
    setSelectedOrder(order.id);
    setShowProcessingMenu(true);
    navigate(`/order-processing/${order.id}`);
  };

  const handleProcessOrder = async (orderId) => {
    try {
      await orderService.processOrder(orderId);
      refetch();
    } catch (error) {
      console.error('Error processing order:', error);
    }
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
      case 'MISSING_INFO':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'EMAIL_SENT':
        return <Mail className="h-5 w-5 text-purple-600" />;
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
      case 'VALIDATED':
        return 'status-badge status-validated';
      case 'MISSING_INFO':
        return 'status-badge bg-red-100 text-red-800';
      case 'EMAIL_SENT':
        return 'status-badge bg-purple-100 text-purple-800';
      default:
        return 'status-badge bg-gray-100 text-gray-800';
    }
  };

  const getProcessingActions = (order) => {
    const actions = [];
    
    switch (order.status) {
      case 'UPLOADED':
        actions.push(
          <button
            key="process"
            onClick={() => handleProcessOrder(order.id)}
            className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700"
          >
            <Play className="h-4 w-4 mr-1" />
            Process
          </button>
        );
        break;
      case 'PROCESSING':
        actions.push(
          <button
            key="pause"
            className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-yellow-600 text-white hover:bg-yellow-700"
            disabled
          >
            <Pause className="h-4 w-4 mr-1" />
            Pause
          </button>
        );
        break;
      case 'PENDING_INFO':
      case 'MISSING_INFO':
        actions.push(
          <button
            key="correct"
            onClick={() => handleOrderSelect(order)}
            className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-orange-600 text-white hover:bg-orange-700"
          >
            <Settings className="h-4 w-4 mr-1" />
            Correct
          </button>
        );
        break;
      default:
        break;
    }

    actions.push(
      <button
        key="view"
        onClick={() => handleOrderSelect(order)}
        className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-gray-600 text-white hover:bg-gray-700"
      >
        <Eye className="h-4 w-4 mr-1" />
        View
      </button>
    );

    return actions;
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="sm:flex sm:items-center justify-between">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Order Processing</h1>
            <p className="mt-2 text-sm text-gray-700">
              Manage and process orders with advanced validation and communication features.
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search orders..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="UPLOADED">Uploaded</option>
                <option value="PROCESSING">Processing</option>
                <option value="PENDING_INFO">Pending Info</option>
                <option value="MISSING_INFO">Missing Info</option>
                <option value="VALIDATED">Validated</option>
                <option value="EMAIL_SENT">Email Sent</option>
              </select>
            </div>
          </div>
        </div>

        {/* Processing Statistics */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-blue-500">
                  <Package className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                  <dd className="text-lg font-medium text-gray-900">{orders.length}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-yellow-500">
                  <Clock className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Processing</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {orders.filter(o => o.status === 'PROCESSING').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-orange-500">
                  <AlertCircle className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Needs Attention</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {orders.filter(o => ['PENDING_INFO', 'MISSING_INFO'].includes(o.status)).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-green-500">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Validated</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {orders.filter(o => o.status === 'VALIDATED').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Orders</h2>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {filteredOrders.length} of {orders.length} orders
              </span>
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading orders...</p>
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-8">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No orders found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filter criteria.
              </p>
            </div>
          ) : (
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order Number
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                              <FileText className="h-5 w-5 text-blue-600" />
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {order.order_number}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {order.id.slice(0, 8)}...
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {order.original_filename || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getStatusBadgeClass(order.status)}>
                          {getStatusIcon(order.status)}
                          <span className="ml-1">{order.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${order.status === 'VALIDATED' ? 100 : 
                                      order.status === 'PROCESSING' ? 50 : 
                                      order.status === 'UPLOADED' ? 20 : 75}%`
                            }}
                          ></div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center space-x-2">
                          {getProcessingActions(order)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Order Processing Modal */}
      {showProcessingMenu && selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Order Processing - {orderDetails?.order_number}
              </h2>
              <button
                onClick={() => {
                  setShowProcessingMenu(false);
                  setSelectedOrder(null);
                  navigate('/order-processing');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <MoreHorizontal className="h-6 w-6" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <OrderProcessingMainMenu
                orderId={selectedOrder}
                onClose={() => {
                  setShowProcessingMenu(false);
                  setSelectedOrder(null);
                  navigate('/order-processing');
                }}
              />
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default OrderProcessingPage;
