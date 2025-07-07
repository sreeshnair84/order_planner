import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import Layout from '../components/common/Layout';
import { orderService } from '../services/orderService';
import { analyticsService } from '../services/analyticsService';
import RetailerManagement from '../components/management/RetailerManagement';
import ManufacturerManagement from '../pages/ManufacturerManagement';
import RouteManagement from '../components/management/RouteManagement';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { 
  Building,
  Users,
  MapPin,
  Package,
  Settings,
  TrendingUp,
  Database,
  Truck,
  Factory,
  Mail,
  Calendar,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle,
  Filter,
  Download,
  RefreshCw,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const FMCGOrderAggregationPage = () => {
  const [activeTab, setActiveTab] = useState('analytics');
  const [selectedDateRange, setSelectedDateRange] = useState('30days');

  // Convert date range to days for API
  const getDateRangeInDays = (range) => {
    switch (range) {
      case '7days': return 7;
      case '30days': return 30;
      case '90days': return 90;
      case '365days': return 365;
      default: return 30;
    }
  };

  const dateRangeInDays = getDateRangeInDays(selectedDateRange);

  // API Queries
  const { data: ordersData } = useQuery(
    'orders',
    () => orderService.getOrders({ page: 1, per_page: 100 }),
    {
      refetchInterval: 60000,
    }
  );

  const { data: dashboardStats, isLoading: statsLoading } = useQuery(
    ['dashboard-stats', dateRangeInDays],
    () => analyticsService.getDashboardStats(dateRangeInDays),
    {
      refetchInterval: 60000,
    }
  );

  const { data: performanceMetrics, isLoading: metricsLoading } = useQuery(
    ['performance-metrics', dateRangeInDays],
    () => analyticsService.getPerformanceMetrics(dateRangeInDays),
    {
      refetchInterval: 60000,
    }
  );

  const { data: statusDistribution, isLoading: distributionLoading } = useQuery(
    ['status-distribution', dateRangeInDays],
    () => analyticsService.getOrderStatusDistribution(dateRangeInDays),
    {
      refetchInterval: 60000,
    }
  );

  const { data: monthlyTrends, isLoading: trendsLoading } = useQuery(
    ['monthly-trends', dateRangeInDays],
    () => analyticsService.getMonthlyTrends(6), // Last 6 months
    {
      refetchInterval: 300000, // 5 minutes
    }
  );

  const { data: deliveryPerformance, isLoading: deliveryLoading } = useQuery(
    ['delivery-performance', dateRangeInDays],
    () => analyticsService.getDeliveryPerformance(dateRangeInDays),
    {
      refetchInterval: 300000,
    }
  );

  const { data: orderAggregation, isLoading: aggregationLoading } = useQuery(
    ['order-aggregation', dateRangeInDays],
    () => analyticsService.getOrderAggregation('category', dateRangeInDays),
    {
      refetchInterval: 300000,
    }
  );

  const orders = ordersData?.orders || [];
  const isLoading = statsLoading || metricsLoading || distributionLoading || trendsLoading;

  // Refresh function to refetch all queries
  const refreshData = () => {
    // Refetch all queries
    window.location.reload(); // Simple refresh for now
  };

  // Chart data - using real analytics data
  const orderStatusData = {
    labels: statusDistribution?.map(d => d.status.replace(/_/g, ' ').toUpperCase()) || ['UPLOADED', 'PROCESSING', 'VALIDATED', 'DELIVERED', 'PENDING'],
    datasets: [
      {
        data: statusDistribution?.map(d => d.count) || [0, 0, 0, 0, 0],
        backgroundColor: [
          '#3B82F6',
          '#F59E0B',
          '#10B981',
          '#059669',
          '#F97316',
        ],
        borderWidth: 0,
      },
    ],
  };

  const monthlyOrdersData = {
    labels: monthlyTrends?.map(t => t.month) || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Orders',
        data: monthlyTrends?.map(t => t.order_count) || [0, 0, 0, 0, 0, 0],
        backgroundColor: '#3B82F6',
        borderColor: '#2563EB',
        borderWidth: 2,
      },
    ],
  };

  const deliveryPerformanceData = {
    labels: deliveryPerformance?.map(d => d.week) || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'On-Time Delivery %',
        data: deliveryPerformance?.map(d => d.on_time_delivery) || [0, 0, 0, 0],
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
      },
      {
        label: 'Average Delivery Time (hrs)',
        data: deliveryPerformance?.map(d => d.avg_delivery_time) || [0, 0, 0, 0],
        borderColor: '#F59E0B',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
      },
    ],
  };

  const tabs = [
    { id: 'analytics', name: 'Analytics Dashboard', icon: BarChart3 },
    { id: 'logistics', name: 'Logistics Management', icon: Truck },
    { id: 'management', name: 'Data Management', icon: Database },
    { id: 'aggregation', name: 'Order Aggregation', icon: Package },
  ];

  const managementTabs = [
    {
      id: 'retailers',
      name: 'Retailers',
      icon: Building,
      description: 'Manage retail partners and their information',
      component: <RetailerManagement />
    },
    {
      id: 'manufacturers',
      name: 'Manufacturers',
      icon: Factory,
      description: 'Manage manufacturing partners and locations',
      component: <ManufacturerManagement />
    },
    {
      id: 'routes',
      name: 'Routes',
      icon: MapPin,
      description: 'Define and manage delivery routes',
      component: <RouteManagement />
    },
    {
      id: 'fleet',
      name: 'Fleet',
      icon: Truck,
      description: 'Manage delivery fleet and truck information',
      component: <div className="p-6 text-center text-gray-500">Fleet management coming soon...</div>
    },
  ];

  const [activeManagementTab, setActiveManagementTab] = useState('retailers');

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">FMCG Order Aggregation</h1>
            <p className="mt-2 text-sm text-gray-700">
              Comprehensive analytics, logistics management, and order aggregation platform.
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <div className="flex space-x-2">
              <select
                value={selectedDateRange}
                onChange={(e) => setSelectedDateRange(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
              </select>
              <button
                onClick={refreshData}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
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
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {/* Key Performance Indicators */}
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Package className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                          <dd className="text-lg font-medium text-gray-900">{dashboardStats?.total_orders || 0}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Clock className="h-8 w-8 text-yellow-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Avg Processing Time</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.average_processing_time || dashboardStats?.avg_processing_time_hours || 0}h</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">On-Time Delivery</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.on_time_delivery_rate || dashboardStats?.on_time_delivery_rate || 0}%</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <DollarSign className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Cost per Delivery</dt>
                          <dd className="text-lg font-medium text-gray-900">${performanceMetrics?.cost_per_delivery || 0}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Order Status Distribution</h3>
                  <div className="h-64">
                    <Doughnut data={orderStatusData} options={{ maintainAspectRatio: false }} />
                  </div>
                </div>

                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Orders</h3>
                  <div className="h-64">
                    <Bar data={monthlyOrdersData} options={{ maintainAspectRatio: false }} />
                  </div>
                </div>

                <div className="bg-white shadow rounded-lg p-6 lg:col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Delivery Performance Trends</h3>
                  <div className="h-64">
                    <Line data={deliveryPerformanceData} options={{ maintainAspectRatio: false }} />
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {orders.slice(0, 5).map((order) => (
                    <div key={order.id} className="px-6 py-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <Activity className="h-5 w-5 text-gray-400" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            Order {order.order_number} - {order.status}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'logistics' && (
            <div className="space-y-6">
              {/* Logistics Overview */}
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Truck className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Active Vehicles</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.active_vehicles || 0}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <MapPin className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Active Routes</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.active_routes || 0}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <TrendingUp className="h-8 w-8 text-purple-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Fuel Efficiency</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.fuel_efficiency || 0}%</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">System Uptime</dt>
                          <dd className="text-lg font-medium text-gray-900">{performanceMetrics?.system_uptime || 0}%</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Trip Planning and Optimization */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Trip Planning & Optimization</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <MapPin className="h-5 w-5 mr-2 text-blue-600" />
                    Optimize Routes
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Truck className="h-5 w-5 mr-2 text-green-600" />
                    Plan Trips
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Calendar className="h-5 w-5 mr-2 text-purple-600" />
                    Schedule Deliveries
                  </button>
                </div>
              </div>

              {/* Real-time Tracking */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Real-time Tracking</h3>
                <div className="bg-gray-100 rounded-lg p-8 text-center">
                  <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-500">Interactive map view coming soon</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'management' && (
            <div className="space-y-6">
              {/* Management Overview */}
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {managementTabs.map((tab) => (
                  <div key={tab.id} className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <tab.icon className="h-8 w-8 text-blue-600" />
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">{tab.name}</dt>
                            <dd className="text-xs text-gray-400">{tab.description}</dd>
                          </dl>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Management Tabs */}
              <div className="bg-white shadow rounded-lg">
                <div className="border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8 px-6">
                    {managementTabs.map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveManagementTab(tab.id)}
                        className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                          activeManagementTab === tab.id
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
                <div className="p-6">
                  {managementTabs.find(tab => tab.id === activeManagementTab)?.component}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'aggregation' && (
            <div className="space-y-6">
              {/* Aggregation Controls */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Order Aggregation Controls</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Package className="h-5 w-5 mr-2 text-blue-600" />
                    Aggregate by Region
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Calendar className="h-5 w-5 mr-2 text-green-600" />
                    Aggregate by Date
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Building className="h-5 w-5 mr-2 text-purple-600" />
                    Aggregate by Retailer
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <Factory className="h-5 w-5 mr-2 text-orange-600" />
                    Aggregate by Product
                  </button>
                </div>
              </div>

              {/* Aggregation Results */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Aggregation Results</h3>
                  <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Orders
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Value
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Action
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {orderAggregation && orderAggregation.length > 0 ? (
                        orderAggregation.map((item, index) => (
                          <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {item.category}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.total_orders}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              ${item.total_value?.toLocaleString() || 0}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                item.status === 'Completed' ? 'bg-green-100 text-green-800' :
                                item.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {item.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button className="text-blue-600 hover:text-blue-900">View Details</button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                            {aggregationLoading ? 'Loading aggregation data...' : 'No aggregation data available'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default FMCGOrderAggregationPage;
