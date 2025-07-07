import React, { useState, useEffect } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
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

const LogisticsDashboard = () => {
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [tripAnalytics, setTripAnalytics] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [realTimeTracking, setRealTimeTracking] = useState(null);
  const [optimizationLogs, setOptimizationLogs] = useState([]);
  const [selectedDateRange, setSelectedDateRange] = useState('30days');
  const [isLoading, setIsLoading] = useState(true);
  // eslint-disable-next-line no-unused-vars
  const [activeMetric, setActiveMetric] = useState('efficiency');

  useEffect(() => {
    loadDashboardData();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      loadRealTimeData();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDateRange]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadPerformanceMetrics(),
        loadTripAnalytics(),
        loadOptimizationLogs(),
      ]);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPerformanceMetrics = async () => {
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      switch (selectedDateRange) {
        case '7days':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30days':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90days':
          startDate.setDate(startDate.getDate() - 90);
          break;
        default:
          startDate.setDate(startDate.getDate() - 30);
      }

      const response = await fetch(
        `/api/logistics/performance-metrics?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setPerformanceMetrics(data);
      } else {
        console.error('Failed to load performance metrics:', response.status);
        // Set fallback data
        setPerformanceMetrics({
          summary: {
            total_routes: 0,
            avg_capacity_utilization: 0,
            total_distance_km: 0,
          },
          efficiency_metrics: {},
          cost_metrics: {
            estimated_cost_savings: 0
          },
          sustainability_metrics: {}
        });
      }
    } catch (error) {
      console.error('Error loading performance metrics:', error);
      // Set fallback data on error
      setPerformanceMetrics({
        summary: {
          total_routes: 0,
          avg_capacity_utilization: 0,
          total_distance_km: 0,
        },
        efficiency_metrics: {},
        cost_metrics: {
          estimated_cost_savings: 0
        },
        sustainability_metrics: {}
      });
    }
  };

  const loadTripAnalytics = async () => {
    try {
      const response = await fetch('/api/trips/analytics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setTripAnalytics(data);
    } catch (error) {
      console.error('Error loading trip analytics:', error);
    }
  };

  const loadOptimizationLogs = async () => {
    try {
      const response = await fetch('/api/logistics/optimization-logs?limit=10', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setOptimizationLogs(data);
    } catch (error) {
      console.error('Error loading optimization logs:', error);
    }
  };

  const loadRealTimeData = async () => {
    try {
      // This would typically fetch real-time tracking data
      // For now, we'll simulate with a mock update
      console.log('Updating real-time data...');
    } catch (error) {
      console.error('Error loading real-time data:', error);
    }
  };

  const MetricCard = ({ title, value, unit, trend, color, icon }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
          {icon}
        </div>
        <div className={`text-sm font-medium ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </div>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>}
      </h3>
      <p className="text-sm text-gray-600">{title}</p>
    </div>
  );

  const renderPerformanceMetrics = () => {
    if (!performanceMetrics) return null;

    // eslint-disable-next-line no-unused-vars
    const { summary, efficiency_metrics, cost_metrics, sustainability_metrics } = performanceMetrics;

    // Add null checks for summary object
    if (!summary) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-50 p-6 rounded-lg">
            <p className="text-gray-500">No performance data available</p>
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Routes"
          value={summary.total_routes || 0}
          trend={5.2}
          color="bg-blue-100"
          icon={<svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" /></svg>}
        />
        <MetricCard
          title="Avg Capacity Utilization"
          value={((summary.avg_capacity_utilization || 0) * 100).toFixed(1)}
          unit="%"
          trend={2.8}
          color="bg-green-100"
          icon={<svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" /></svg>}
        />
        <MetricCard
          title="Total Distance"
          value={(summary.total_distance_km || 0).toFixed(0)}
          unit="km"
          trend={-1.5}
          color="bg-orange-100"
          icon={<svg className="w-6 h-6 text-orange-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>}
        />
        <MetricCard
          title="Cost Savings"
          value={(cost_metrics?.estimated_cost_savings || 0).toFixed(0)}
          unit="$"
          trend={8.3}
          color="bg-purple-100"
          icon={<svg className="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 20 20"><path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" /><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" /></svg>}
        />
      </div>
    );
  };

  const renderEfficiencyChart = () => {
    if (!performanceMetrics?.efficiency_metrics) return null;

    const data = {
      labels: ['Improvement %', 'Success Rate', 'Execution Time'],
      datasets: [
        {
          label: 'Performance Metrics',
          data: [
            performanceMetrics.efficiency_metrics.avg_improvement_percentage,
            performanceMetrics.efficiency_metrics.success_rate,
            performanceMetrics.efficiency_metrics.avg_execution_time_seconds,
          ],
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(245, 158, 11, 0.8)',
          ],
          borderColor: [
            'rgba(59, 130, 246, 1)',
            'rgba(16, 185, 129, 1)',
            'rgba(245, 158, 11, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: 'Optimization Efficiency Metrics',
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <Bar data={data} options={options} />
      </div>
    );
  };

  const renderSustainabilityChart = () => {
    if (!performanceMetrics?.sustainability_metrics) return null;

    const data = {
      labels: ['Emission Reduction', 'Fuel Savings', 'Carbon Footprint Reduction'],
      datasets: [
        {
          data: [
            performanceMetrics.sustainability_metrics.emission_reduction_percentage,
            performanceMetrics.sustainability_metrics.fuel_savings_liters,
            performanceMetrics.sustainability_metrics.carbon_footprint_reduction_kg,
          ],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(168, 85, 247, 0.8)',
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(59, 130, 246, 1)',
            'rgba(168, 85, 247, 1)',
          ],
          borderWidth: 2,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
        },
        title: {
          display: true,
          text: 'Sustainability Impact',
        },
      },
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <Doughnut data={data} options={options} />
      </div>
    );
  };

  const renderOptimizationLogs = () => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4">Recent Optimizations</h3>
      <div className="space-y-4">
        {optimizationLogs.map((log, index) => (
          <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${
                log.status === 'SUCCESS' ? 'bg-green-500' : 
                log.status === 'FAILED' ? 'bg-red-500' : 'bg-yellow-500'
              }`} />
              <div>
                <p className="font-medium">{log.optimization_algorithm}</p>
                <p className="text-sm text-gray-600">
                  {new Date(log.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-medium">{log.improvement_percentage.toFixed(1)}%</p>
              <p className="text-sm text-gray-600">{log.execution_time_seconds.toFixed(1)}s</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderRealTimeAlerts = () => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4">Real-Time Alerts</h3>
      <div className="space-y-3">
        <div className="flex items-center p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3"></div>
          <div className="flex-1">
            <p className="text-sm font-medium">Route Optimization Opportunity</p>
            <p className="text-xs text-gray-600">3 new orders available for consolidation</p>
          </div>
          <span className="text-xs text-gray-500">2 min ago</span>
        </div>
        <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
          <div className="flex-1">
            <p className="text-sm font-medium">Trip Completed Successfully</p>
            <p className="text-xs text-gray-600">Route R-001 delivered all 12 orders</p>
          </div>
          <span className="text-xs text-gray-500">15 min ago</span>
        </div>
        <div className="flex items-center p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
          <div className="flex-1">
            <p className="text-sm font-medium">New Manufacturing Location</p>
            <p className="text-xs text-gray-600">Plant B is now available for trip planning</p>
          </div>
          <span className="text-xs text-gray-500">1 hour ago</span>
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Logistics Dashboard</h1>
            <div className="flex items-center space-x-4">
              <select
                value={selectedDateRange}
                onChange={(e) => setSelectedDateRange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="7days">Last 7 days</option>
                <option value="30days">Last 30 days</option>
                <option value="90days">Last 90 days</option>
              </select>
              <button
                onClick={loadDashboardData}
                className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Performance Metrics */}
        {renderPerformanceMetrics()}

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {renderEfficiencyChart()}
          {renderSustainabilityChart()}
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {renderOptimizationLogs()}
          {renderRealTimeAlerts()}
        </div>
      </div>
    </div>
  );
};

export default LogisticsDashboard;
