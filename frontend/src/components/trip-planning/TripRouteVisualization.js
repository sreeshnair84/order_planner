import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const TripRouteVisualization = ({ optimizedRoutes, consolidationResults, realTimeData }) => {
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [viewMode, setViewMode] = useState('overview'); // 'overview', 'detailed', 'constraints', 'performance'
  const [routeMetrics, setRouteMetrics] = useState(null);

  const calculateRouteMetrics = useCallback(() => {
    const metrics = {
      totalDistance: optimizedRoutes.reduce((sum, route) => sum + route.total_distance_km, 0),
      totalDuration: optimizedRoutes.reduce((sum, route) => sum + route.estimated_duration_hours, 0),
      averageEfficiency: optimizedRoutes.reduce((sum, route) => sum + (route.optimization_score || 0), 0) / optimizedRoutes.length,
      capacityUtilization: optimizedRoutes.reduce((sum, route) => sum + (route.capacity_utilization || 0), 0) / optimizedRoutes.length,
      deliveryTimelineData: generateDeliveryTimeline(),
      efficiencyTrendData: generateEfficiencyTrend(),
      constraintComplianceData: generateConstraintCompliance()
    };
    
    setRouteMetrics(metrics);
  }, [optimizedRoutes, generateDeliveryTimeline, generateEfficiencyTrend, generateConstraintCompliance]);

  useEffect(() => {
    if (optimizedRoutes && optimizedRoutes.length > 0) {
      calculateRouteMetrics();
    }
  }, [optimizedRoutes, calculateRouteMetrics]);

  const generateDeliveryTimeline = useCallback(() => {
    const timeline = [];
    optimizedRoutes.forEach((route, routeIndex) => {
      route.delivery_sequence.forEach((delivery, deliveryIndex) => {
        const estimatedTime = new Date();
        estimatedTime.setHours(8 + deliveryIndex * 0.5); // Mock timeline
        
        timeline.push({
          routeId: route.route_id,
          routeName: route.route_name,
          orderId: delivery.order_id,
          sequence: delivery.sequence,
          estimatedTime: estimatedTime.toISOString(),
          status: delivery.delivery_status,
          delay: realTimeData?.deliveryDelays?.[delivery.order_id]?.estimatedDelay || 0
        });
      });
    });
    return timeline.sort((a, b) => new Date(a.estimatedTime) - new Date(b.estimatedTime));
  }, [optimizedRoutes, realTimeData]);

  const generateEfficiencyTrend = useCallback(() => {
    return optimizedRoutes.map((route, index) => ({
      routeIndex: index + 1,
      routeName: route.route_name,
      efficiency: (route.optimization_score || 0) * 100,
      distance: route.total_distance_km,
      duration: route.estimated_duration_hours,
      capacity: (route.capacity_utilization || 0) * 100
    }));
  }, [optimizedRoutes]);

  const generateConstraintCompliance = useCallback(() => {
    const compliance = {
      satisfied: optimizedRoutes.filter(route => route.constraints_satisfied).length,
      violated: optimizedRoutes.filter(route => !route.constraints_satisfied).length,
      total: optimizedRoutes.length
    };
    
    return [
      { name: 'Satisfied', value: compliance.satisfied, color: '#10B981' },
      { name: 'Violated', value: compliance.violated, color: '#EF4444' }
    ];
  }, [optimizedRoutes]);

  const getDeliveryStatusColor = (status, delay = 0) => {
    if (delay > 0) return '#EF4444'; // Red for delayed
    switch (status) {
      case 'DELIVERED': return '#10B981'; // Green
      case 'IN_TRANSIT': return '#3B82F6'; // Blue
      case 'SCHEDULED': return '#F59E0B'; // Yellow
      default: return '#6B7280'; // Gray
    }
  };

  const formatTime = (timeString) => {
    return new Date(timeString).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderOverviewMode = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Route Efficiency Trend */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="text-lg font-semibold mb-4">Route Efficiency Analysis</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={routeMetrics.efficiencyTrendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="routeIndex" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="efficiency" stroke="#3B82F6" strokeWidth={2} name="Efficiency %" />
            <Line type="monotone" dataKey="capacity" stroke="#10B981" strokeWidth={2} name="Capacity %" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Constraint Compliance */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="text-lg font-semibold mb-4">Constraint Compliance</h4>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={routeMetrics.constraintComplianceData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {routeMetrics.constraintComplianceData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderDetailedMode = () => (
    <div className="space-y-6">
      {/* Route Selection */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="text-lg font-semibold mb-4">Route Details</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {optimizedRoutes.map(route => (
            <button
              key={route.route_id}
              onClick={() => setSelectedRoute(route)}
              className={`p-4 rounded-lg border-2 text-left transition-colors ${
                selectedRoute?.route_id === route.route_id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h5 className="font-medium">{route.route_name}</h5>
              <p className="text-sm text-gray-600">
                {route.delivery_sequence.length} stops • {route.total_distance_km.toFixed(1)} km
              </p>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((route.optimization_score || 0) * 100, 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((route.optimization_score || 0) * 100).toFixed(1)}% optimized
                </p>
              </div>
            </button>
          ))}
        </div>

        {/* Selected Route Details */}
        {selectedRoute && (
          <div className="border-t pt-6">
            <h5 className="font-medium mb-4">{selectedRoute.route_name} - Delivery Sequence</h5>
            <div className="space-y-3">
              {selectedRoute.delivery_sequence.map((delivery, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                      style={{ backgroundColor: getDeliveryStatusColor(delivery.delivery_status, realTimeData?.deliveryDelays?.[delivery.order_id]?.estimatedDelay) }}
                    >
                      {delivery.sequence}
                    </div>
                    <div>
                      <p className="font-medium">Order {delivery.order_id}</p>
                      <p className="text-sm text-gray-600">{delivery.address}</p>
                      {realTimeData?.deliveryDelays?.[delivery.order_id] && (
                        <p className="text-sm text-red-600">
                          Delayed by {realTimeData.deliveryDelays[delivery.order_id].estimatedDelay} min
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {delivery.estimated_arrival ? formatTime(delivery.estimated_arrival) : 'TBD'}
                    </p>
                    <p className="text-xs text-gray-500">{delivery.delivery_status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderConstraintsMode = () => (
    <div className="bg-white p-6 rounded-lg border">
      <h4 className="text-lg font-semibold mb-4">Route Constraints Analysis</h4>
      <div className="space-y-6">
        {optimizedRoutes.map(route => (
          <div key={route.route_id} className="border rounded-lg p-4">
            <h5 className="font-medium mb-3">{route.route_name}</h5>
            
            {/* Constraint Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Distance</p>
                <p className="text-lg font-semibold">{route.total_distance_km.toFixed(1)} km</p>
                <p className="text-xs text-gray-500">Max: 500 km</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Duration</p>
                <p className="text-lg font-semibold">{route.estimated_duration_hours.toFixed(1)} hrs</p>
                <p className="text-xs text-gray-500">Max: 8 hrs</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Stops</p>
                <p className="text-lg font-semibold">{route.delivery_sequence.length}</p>
                <p className="text-xs text-gray-500">Max: 20</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Capacity</p>
                <p className="text-lg font-semibold">{((route.capacity_utilization || 0) * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-500">Target: 90-100%</p>
              </div>
            </div>

            {/* Constraint Status */}
            <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-sm ${
                route.constraints_satisfied 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {route.constraints_satisfied ? 'All Constraints Satisfied' : 'Constraint Violations'}
              </span>
              <span className="text-sm text-gray-600">
                Optimization Score: {((route.optimization_score || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPerformanceMode = () => (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-600">Total Distance</h4>
          <p className="text-2xl font-bold text-blue-600">{routeMetrics?.totalDistance.toFixed(1)} km</p>
        </div>
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-600">Total Duration</h4>
          <p className="text-2xl font-bold text-green-600">{routeMetrics?.totalDuration.toFixed(1)} hrs</p>
        </div>
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-600">Avg Efficiency</h4>
          <p className="text-2xl font-bold text-purple-600">{(routeMetrics?.averageEfficiency * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-600">Capacity Util</h4>
          <p className="text-2xl font-bold text-orange-600">{(routeMetrics?.capacityUtilization * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* Delivery Timeline */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="text-lg font-semibold mb-4">Delivery Timeline</h4>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {routeMetrics?.deliveryTimelineData.map((delivery, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getDeliveryStatusColor(delivery.status, delivery.delay) }}
                ></div>
                <div>
                  <p className="text-sm font-medium">{delivery.routeName} - Order {delivery.orderId}</p>
                  <p className="text-xs text-gray-600">Sequence #{delivery.sequence}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">{formatTime(delivery.estimatedTime)}</p>
                {delivery.delay > 0 && (
                  <p className="text-xs text-red-600">+{delivery.delay} min delay</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* View Mode Selector */}
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex space-x-4">
          <button
            onClick={() => setViewMode('overview')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'overview' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setViewMode('detailed')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'detailed' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Detailed View
          </button>
          <button
            onClick={() => setViewMode('constraints')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'constraints' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Constraints
          </button>
          <button
            onClick={() => setViewMode('performance')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'performance' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Performance
          </button>
        </div>
      </div>

      {/* Content based on view mode */}
      {routeMetrics && (
        <>
          {viewMode === 'overview' && renderOverviewMode()}
          {viewMode === 'detailed' && renderDetailedMode()}
          {viewMode === 'constraints' && renderConstraintsMode()}
          {viewMode === 'performance' && renderPerformanceMode()}
        </>
      )}
    </div>
  );
};

export default TripRouteVisualization;
