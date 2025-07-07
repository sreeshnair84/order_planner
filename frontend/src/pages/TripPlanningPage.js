import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import SKUOptimizationDashboard from '../components/trip-planning/SKUOptimizationDashboard';
import RealTimeRouteAdjustment from '../components/trip-planning/RealTimeRouteAdjustment';
import SKUDeliveryConstraints from '../components/trip-planning/SKUDeliveryConstraints';
import RetailerTimeWindowManager from '../components/trip-planning/RetailerTimeWindowManager';
import TripRouteVisualization from '../components/trip-planning/TripRouteVisualization';
import Layout from '../components/common/Layout';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const TripPlanningPage = () => {
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [manufacturingLocations, setManufacturingLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [optimizedRoutes, setOptimizedRoutes] = useState([]);
  const [consolidationResults, setConsolidationResults] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [mapCenter, setMapCenter] = useState([40.7128, -74.0060]); // Default to NYC
  const [mapZoom, setMapZoom] = useState(10);
  const [activeTab, setActiveTab] = useState('orders');
  const [optimizationParams, setOptimizationParams] = useState({});
  const [deliveryConstraints, setDeliveryConstraints] = useState({});
  const [timeWindows, setTimeWindows] = useState({});
  const [realTimeData, setRealTimeData] = useState({});

  // Load initial data
  useEffect(() => {
    loadAvailableOrders();
    loadManufacturingLocations();
  }, []);

  const loadAvailableOrders = async () => {
    try {
      const response = await fetch('/api/orders', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setAvailableOrders(data.orders || []);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  const loadManufacturingLocations = async () => {
    try {
      const response = await fetch('/api/trips/manufacturing-locations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      // Defensive: ensure data is always an array
      let locations = data;
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        // Try common wrappers
        if (Array.isArray(data.locations)) {
          locations = data.locations;
        } else if (Array.isArray(data.data)) {
          locations = data.data;
        } else {
          // Unexpected shape, fallback to empty array
          locations = [];
        }
      }
      if (!Array.isArray(locations)) {
        console.error('manufacturingLocations API did not return an array:', data);
        locations = [];
      }
      setManufacturingLocations(locations);
      // For debugging
      if (process.env.NODE_ENV !== 'production') {
        console.log('Loaded manufacturing locations:', locations);
      }
    } catch (error) {
      console.error('Error loading manufacturing locations:', error);
    }
  };

  const handleOptimizeTrips = async () => {
    if (!selectedLocation || selectedOrders.length === 0) {
      alert('Please select a manufacturing location and at least one order');
      return;
    }

    setIsOptimizing(true);
    
    try {
      // Step 1: Optimize SKU consolidation
      const consolidationResponse = await fetch('/api/trips/optimize-skus', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          retailer_id: selectedOrders[0]?.retailer_id || 'default',
          manufacturing_location_id: selectedLocation,
          start_date: new Date().toISOString(),
          end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        }),
      });

      const consolidationData = await consolidationResponse.json();
      setConsolidationResults(consolidationData);

      // Step 2: Optimize routes
      const routeResponse = await fetch('/api/trips/optimize-routes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          order_ids: selectedOrders.map(order => order.id),
          manufacturing_location_id: selectedLocation,
          planned_date: new Date().toISOString(),
        }),
      });

      const routeData = await routeResponse.json();
      setOptimizedRoutes([routeData]);

      // Update map center to manufacturing location
      const selectedMfgLocation = manufacturingLocations.find(loc => loc.id === selectedLocation);
      if (selectedMfgLocation) {
        setMapCenter([selectedMfgLocation.latitude, selectedMfgLocation.longitude]);
        setMapZoom(12);
      }

      setActiveTab('routes');
    } catch (error) {
      console.error('Error optimizing trips:', error);
      alert('Error optimizing trips. Please try again.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleOrderSelection = (orderId) => {
    setSelectedOrders(prev => {
      if (prev.find(order => order.id === orderId)) {
        return prev.filter(order => order.id !== orderId);
      } else {
        const order = availableOrders.find(o => o.id === orderId);
        return [...prev, order];
      }
    });
  };

  const renderOrdersTab = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Select Orders for Trip Planning</h2>
      
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Manufacturing Location</label>
        <select
          value={selectedLocation}
          onChange={(e) => setSelectedLocation(e.target.value)}
          className="w-full p-2 border rounded-md"
        >
          <option value="">Select Manufacturing Location</option>
          {manufacturingLocations.map(location => (
            <option key={location.id} value={location.id}>
              {location.name} - {location.address}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {availableOrders.map(order => (
          <div
            key={order.id}
            className={`p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedOrders.find(o => o.id === order.id)
                ? 'bg-blue-50 border-blue-500'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
            onClick={() => handleOrderSelection(order.id)}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">{order.order_number}</h3>
              <span className={`px-2 py-1 text-xs rounded ${
                order.status === 'CONFIRMED' ? 'bg-green-100 text-green-800' :
                order.status === 'PROCESSING' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {order.status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">
              Priority: {order.priority}
            </p>
            <p className="text-sm text-gray-600 mb-1">
              SKUs: {order.total_sku_count}
            </p>
            <p className="text-sm text-gray-600">
              Total: ${order.total.toFixed(2)}
            </p>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Selected Orders: {selectedOrders.length}
        </div>
        <button
          onClick={handleOptimizeTrips}
          disabled={isOptimizing || selectedOrders.length === 0 || !selectedLocation}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isOptimizing ? 'Optimizing...' : 'Optimize Trips'}
        </button>
      </div>
    </div>
  );

  const renderConsolidationTab = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">SKU Consolidation Results</h2>
      
      {consolidationResults ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-2">Total SKUs</h3>
              <p className="text-3xl font-bold text-blue-600">{consolidationResults.total_skus}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-2">Trip Groups</h3>
              <p className="text-3xl font-bold text-green-600">{consolidationResults.trip_groups.length}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-2">Efficiency</h3>
              <p className="text-3xl font-bold text-orange-600">{(consolidationResults.optimization_efficiency * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-2">Weight</h3>
              <p className="text-3xl font-bold text-purple-600">{consolidationResults.total_weight_kg.toFixed(1)} kg</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Trip Groups</h3>
            <div className="space-y-4">
              {consolidationResults.trip_groups.map((group, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">Group {index + 1}</h4>
                    <span className="text-sm text-gray-500">
                      {group.sku_count} SKUs
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                    <div>Weight: {group.total_weight_kg.toFixed(1)} kg</div>
                    <div>Volume: {group.total_volume_m3.toFixed(1)} m³</div>
                    <div>Efficiency: {(group.delivery_efficiency * 100).toFixed(1)}%</div>
                    <div>Center: {group.geographic_center[0].toFixed(4)}, {group.geographic_center[1].toFixed(4)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">No consolidation results available. Please optimize trips first.</p>
        </div>
      )}
    </div>
  );

  const renderRoutesTab = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Optimized Routes</h2>
      
      {optimizedRoutes.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {optimizedRoutes.map((route, index) => (
              <div key={index} className="bg-white p-4 rounded-lg border">
                <h3 className="text-lg font-semibold mb-2">{route.route_name}</h3>
                <div className="space-y-2 text-sm">
                  <div>Distance: {route.total_distance_km.toFixed(1)} km</div>
                  <div>Duration: {route.estimated_duration_hours.toFixed(1)} hours</div>
                  <div>Score: {route.optimization_score.toFixed(2)}</div>
                  <div>Stops: {route.waypoints.length}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Route Map</h3>
            <div className="h-96 rounded-lg overflow-hidden">
              <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                
                {/* Manufacturing location marker */}
                {manufacturingLocations.find(loc => loc.id === selectedLocation) && (
                  <Marker
                    position={[
                      manufacturingLocations.find(loc => loc.id === selectedLocation).latitude,
                      manufacturingLocations.find(loc => loc.id === selectedLocation).longitude
                    ]}
                    icon={L.divIcon({
                      className: 'custom-marker manufacturing',
                      html: '<div class="w-4 h-4 bg-red-500 rounded-full border-2 border-white"></div>',
                      iconSize: [16, 16],
                      iconAnchor: [8, 8]
                    })}
                  >
                    <Popup>
                      <div>
                        <h4 className="font-semibold">Manufacturing Location</h4>
                        <p>{manufacturingLocations.find(loc => loc.id === selectedLocation).name}</p>
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Route waypoints */}
                {optimizedRoutes.map((route, routeIndex) => (
                  <div key={routeIndex}>
                    {route.waypoints.map((waypoint, waypointIndex) => (
                      <Marker
                        key={waypointIndex}
                        position={[waypoint.latitude, waypoint.longitude]}
                        icon={L.divIcon({
                          className: 'custom-marker delivery',
                          html: `<div class="w-4 h-4 bg-blue-500 rounded-full border-2 border-white text-white text-xs flex items-center justify-center">${waypointIndex + 1}</div>`,
                          iconSize: [16, 16],
                          iconAnchor: [8, 8]
                        })}
                      >
                        <Popup>
                          <div>
                            <h4 className="font-semibold">Delivery Stop {waypointIndex + 1}</h4>
                            <p>{waypoint.name}</p>
                            <p className="text-sm text-gray-600">{waypoint.address}</p>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                    
                    {/* Route line */}
                    {route.waypoints.length > 1 && (
                      <Polyline
                        positions={route.waypoints.map(wp => [wp.latitude, wp.longitude])}
                        color="blue"
                        weight={3}
                        opacity={0.7}
                      />
                    )}
                  </div>
                ))}
              </MapContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Delivery Sequence</h3>
            <div className="space-y-2">
              {optimizedRoutes[0]?.delivery_sequence.map((delivery, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm">
                      {delivery.sequence}
                    </span>
                    <div>
                      <p className="font-medium">Order {delivery.order_id}</p>
                      <p className="text-sm text-gray-600">{delivery.address}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{delivery.delivery_status}</p>
                    {delivery.estimated_arrival && (
                      <p className="text-xs text-gray-500">
                        ETA: {new Date(delivery.estimated_arrival).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">No optimized routes available. Please optimize trips first.</p>
        </div>
      )}
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Trip Analytics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-2">Total Distance</h3>
          <p className="text-3xl font-bold text-blue-600">
            {optimizedRoutes.reduce((sum, route) => sum + route.total_distance_km, 0).toFixed(1)} km
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-2">Total Duration</h3>
          <p className="text-3xl font-bold text-green-600">
            {optimizedRoutes.reduce((sum, route) => sum + route.estimated_duration_hours, 0).toFixed(1)} hrs
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-2">Optimization Score</h3>
          <p className="text-3xl font-bold text-orange-600">
            {optimizedRoutes.length > 0 ? (
              optimizedRoutes.reduce((sum, route) => sum + route.optimization_score, 0) / optimizedRoutes.length
            ).toFixed(2) : '0.00'}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-2">Efficiency</h3>
          <p className="text-3xl font-bold text-purple-600">
            {optimizedRoutes.length > 0 ? (
              optimizedRoutes.reduce((sum, route) => sum + route.improvement_percentage, 0) / optimizedRoutes.length
            ).toFixed(1) : '0.0'}%
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Optimization Summary</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span>Selected Orders:</span>
            <span className="font-medium">{selectedOrders.length}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Optimized Routes:</span>
            <span className="font-medium">{optimizedRoutes.length}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Total Delivery Stops:</span>
            <span className="font-medium">
              {optimizedRoutes.reduce((sum, route) => sum + route.waypoints.length, 0)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Constraints Satisfied:</span>
            <span className={`font-medium ${
              optimizedRoutes.every(route => route.constraints_satisfied) ? 'text-green-600' : 'text-red-600'
            }`}>
              {optimizedRoutes.every(route => route.constraints_satisfied) ? 'Yes' : 'No'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

 

  return (
    <Layout>
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Trip Planning & Optimization</h1>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {activeTab === 'orders' && renderOrdersTab()}
        {activeTab === 'consolidation' && renderConsolidationTab()}
        {activeTab === 'sku-optimization' && (
          <SKUOptimizationDashboard
            consolidationResults={consolidationResults}
            onOptimizationParamsChange={setOptimizationParams}
          />
        )}
        {activeTab === 'routes' && renderRoutesTab()}
        {activeTab === 'real-time' && (
          <RealTimeRouteAdjustment
            optimizedRoutes={optimizedRoutes}
            onRouteUpdate={(updatedRoute) => {
              setOptimizedRoutes(prev => 
                prev.map(route => 
                  route.route_id === updatedRoute.route_id ? updatedRoute : route
                )
              );
            }}
          />
        )}
        {activeTab === 'constraints' && (
          <SKUDeliveryConstraints
            consolidationResults={consolidationResults}
            onConstraintsUpdate={setDeliveryConstraints}
          />
        )}
        {activeTab === 'time-windows' && (
          <RetailerTimeWindowManager
            optimizedRoutes={optimizedRoutes}
            onTimeWindowUpdate={setTimeWindows}
          />
        )}
        {activeTab === 'visualization' && (
          <TripRouteVisualization
            optimizedRoutes={optimizedRoutes}
            consolidationResults={consolidationResults}
            realTimeData={realTimeData}
          />
        )}
        {activeTab === 'analytics' && renderAnalyticsTab()}
      </div>
    </Layout>
  );
};

export default TripPlanningPage;
