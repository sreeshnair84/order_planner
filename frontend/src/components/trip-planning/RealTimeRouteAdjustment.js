import React, { useState, useEffect } from 'react';
// import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
// import L from 'leaflet';

const RealTimeRouteAdjustment = ({ optimizedRoutes, onRouteUpdate }) => {
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [adjustmentMode, setAdjustmentMode] = useState('reorder'); // 'reorder', 'add', 'remove'
  const [realTimeData, setRealTimeData] = useState({
    trafficConditions: {},
    deliveryDelays: {},
    routeAlerts: []
  });
  const [isAdjusting, setIsAdjusting] = useState(false);

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      updateRealTimeData();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const updateRealTimeData = () => {
    // Simulate real-time traffic and delivery data
    const mockTrafficData = {
      light: Math.random() > 0.7,
      moderate: Math.random() > 0.5,
      heavy: Math.random() > 0.8
    };

    const mockDelays = {};
    optimizedRoutes.forEach(route => {
      route.delivery_sequence.forEach(delivery => {
        if (Math.random() > 0.85) { // 15% chance of delay
          mockDelays[delivery.order_id] = {
            estimatedDelay: Math.floor(Math.random() * 60) + 15, // 15-75 minutes
            reason: ['traffic', 'weather', 'delivery_issue'][Math.floor(Math.random() * 3)]
          };
        }
      });
    });

    setRealTimeData({
      trafficConditions: mockTrafficData,
      deliveryDelays: mockDelays,
      routeAlerts: generateRouteAlerts(mockDelays)
    });
  };

  const generateRouteAlerts = (delays) => {
    const alerts = [];
    Object.entries(delays).forEach(([orderId, delay]) => {
      alerts.push({
        id: `alert-${orderId}`,
        type: 'warning',
        message: `Delivery ${orderId} delayed by ${delay.estimatedDelay} minutes due to ${delay.reason}`,
        timestamp: new Date(),
        orderId
      });
    });
    return alerts;
  };

  const handleRouteReorder = async (routeId, newSequence) => {
    setIsAdjusting(true);
    try {
      // Call API to reorder route
      const response = await fetch(`/api/trips/routes/${routeId}/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ new_sequence: newSequence })
      });

      if (response.ok) {
        const updatedRoute = await response.json();
        onRouteUpdate(updatedRoute);
      }
    } catch (error) {
      console.error('Error reordering route:', error);
    } finally {
      setIsAdjusting(false);
    }
  };

  const handleOptimizeForConditions = async (routeId, conditions) => {
    setIsAdjusting(true);
    try {
      const response = await fetch(`/api/trips/routes/${routeId}/optimize-realtime`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          traffic_conditions: conditions.traffic,
          delivery_delays: conditions.delays,
          weather_conditions: conditions.weather
        })
      });

      if (response.ok) {
        const optimizedRoute = await response.json();
        onRouteUpdate(optimizedRoute);
      }
    } catch (error) {
      console.error('Error optimizing route for conditions:', error);
    } finally {
      setIsAdjusting(false);
    }
  };

  const getDeliveryStatusColor = (orderId) => {
    if (realTimeData.deliveryDelays[orderId]) {
      return '#EF4444'; // Red for delayed
    }
    return '#10B981'; // Green for on time
  };

  const getTrafficColor = (level) => {
    switch (level) {
      case 'light': return '#10B981';
      case 'moderate': return '#F59E0B';
      case 'heavy': return '#EF4444';
      default: return '#6B7280';
    }
  };

  return (
    <div className="space-y-6">
      {/* Real-time Alerts */}
      {realTimeData.routeAlerts.length > 0 && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4">Real-time Route Alerts</h3>
          <div className="space-y-3">
            {realTimeData.routeAlerts.map(alert => (
              <div key={alert.id} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{alert.message}</p>
                  <p className="text-xs text-gray-500">{alert.timestamp.toLocaleTimeString()}</p>
                </div>
                <button
                  onClick={() => handleOptimizeForConditions(selectedRoute?.route_id, {
                    traffic: realTimeData.trafficConditions,
                    delays: realTimeData.deliveryDelays,
                    weather: 'normal'
                  })}
                  className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700"
                >
                  Auto-adjust
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Route Selection */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Select Route for Adjustment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <h4 className="font-medium">{route.route_name}</h4>
              <p className="text-sm text-gray-600">
                {route.delivery_sequence.length} stops • {route.total_distance_km.toFixed(1)} km
              </p>
              <div className="flex items-center space-x-2 mt-2">
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                  {route.constraints_satisfied ? 'Optimized' : 'Needs Adjustment'}
                </span>
                {Object.values(realTimeData.deliveryDelays).some(delay => 
                  route.delivery_sequence.some(delivery => delivery.order_id === delay.orderId)
                ) && (
                  <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded">
                    Delays Detected
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Route Adjustment Controls */}
      {selectedRoute && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4">Route Adjustment Controls</h3>
          
          {/* Adjustment Mode Selector */}
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setAdjustmentMode('reorder')}
              className={`px-4 py-2 rounded-md ${
                adjustmentMode === 'reorder' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Reorder Stops
            </button>
            <button
              onClick={() => setAdjustmentMode('optimize')}
              className={`px-4 py-2 rounded-md ${
                adjustmentMode === 'optimize' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Auto-Optimize
            </button>
            <button
              onClick={() => setAdjustmentMode('manual')}
              className={`px-4 py-2 rounded-md ${
                adjustmentMode === 'manual' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Manual Edit
            </button>
          </div>

          {/* Delivery Sequence with Real-time Status */}
          <div className="space-y-3">
            <h4 className="font-medium">Delivery Sequence</h4>
            {selectedRoute.delivery_sequence.map((delivery, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-6 h-6 rounded-full flex items-center justify-center text-white text-sm font-medium"
                    style={{ backgroundColor: getDeliveryStatusColor(delivery.order_id) }}
                  >
                    {delivery.sequence}
                  </div>
                  <div>
                    <p className="font-medium">Order {delivery.order_id}</p>
                    <p className="text-sm text-gray-600">{delivery.address}</p>
                    {realTimeData.deliveryDelays[delivery.order_id] && (
                      <p className="text-sm text-red-600">
                        Delayed by {realTimeData.deliveryDelays[delivery.order_id].estimatedDelay} min
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {adjustmentMode === 'reorder' && (
                    <div className="flex space-x-1">
                      <button
                        onClick={() => {
                          // Move up logic
                          if (index > 0) {
                            const newSequence = [...selectedRoute.delivery_sequence];
                            [newSequence[index], newSequence[index - 1]] = [newSequence[index - 1], newSequence[index]];
                            handleRouteReorder(selectedRoute.route_id, newSequence);
                          }
                        }}
                        disabled={index === 0}
                        className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 disabled:opacity-50"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => {
                          // Move down logic
                          if (index < selectedRoute.delivery_sequence.length - 1) {
                            const newSequence = [...selectedRoute.delivery_sequence];
                            [newSequence[index], newSequence[index + 1]] = [newSequence[index + 1], newSequence[index]];
                            handleRouteReorder(selectedRoute.route_id, newSequence);
                          }
                        }}
                        disabled={index === selectedRoute.delivery_sequence.length - 1}
                        className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 disabled:opacity-50"
                      >
                        ↓
                      </button>
                    </div>
                  )}
                  
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {delivery.estimated_arrival ? 
                        new Date(delivery.estimated_arrival).toLocaleTimeString() : 
                        'TBD'
                      }
                    </p>
                    <p className="text-xs text-gray-500">{delivery.delivery_status}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="mt-6 flex space-x-4">
            <button
              onClick={() => handleOptimizeForConditions(selectedRoute.route_id, {
                traffic: realTimeData.trafficConditions,
                delays: realTimeData.deliveryDelays,
                weather: 'normal'
              })}
              disabled={isAdjusting}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isAdjusting ? 'Optimizing...' : 'Optimize for Current Conditions'}
            </button>
            <button
              onClick={() => {
                // Reset to original route
                window.location.reload();
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Reset to Original
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeRouteAdjustment;
