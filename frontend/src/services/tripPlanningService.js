import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for optimization requests
});

// Add auth header to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Trip Planning API calls
export const tripPlanningAPI = {
  // Get available orders for trip planning
  getAvailableOrders: async () => {
    const response = await api.get('/orders');
    return response.data;
  },

  // Get manufacturing locations
  getManufacturingLocations: async () => {
    const response = await api.get('/trips/manufacturing-locations');
    return response.data;
  },

  // Get available trucks
  getTrucks: async (locationId) => {
    const response = await api.get(`/trips/trucks?location_id=${locationId}`);
    return response.data;
  },

  // Optimize trip routes
  optimizeRoutes: async (optimizationData) => {
    const response = await api.post('/trips/optimize-routes', optimizationData);
    return response.data;
  },

  // Optimize SKU consolidation
  optimizeSKUs: async (consolidationData) => {
    const response = await api.post('/trips/optimize-skus', consolidationData);
    return response.data;
  },

  // Get route details
  getRouteDetails: async (routeId) => {
    const response = await api.get(`/trips/routes/${routeId}`);
    return response.data;
  },

  // Get trip analytics
  getTripAnalytics: async (params) => {
    const response = await api.get('/trips/analytics', { params });
    return response.data;
  },

  // Assign truck to route
  assignTruck: async (routeId, truckId) => {
    const response = await api.post(`/trips/routes/${routeId}/assign-truck`, { truck_id: truckId });
    return response.data;
  },
};

// Logistics API calls
export const logisticsAPI = {
  // Get performance metrics
  getPerformanceMetrics: async (params) => {
    const response = await api.get('/logistics/performance-metrics', { params });
    return response.data;
  },

  // Get capacity planning data
  getCapacityPlanning: async (params) => {
    const response = await api.get('/logistics/capacity-planning', { params });
    return response.data;
  },

  // Get real-time tracking
  getRealTimeTracking: async (params) => {
    const response = await api.get('/logistics/real-time-tracking', { params });
    return response.data;
  },

  // Get optimization logs
  getOptimizationLogs: async (params) => {
    const response = await api.get('/logistics/optimization-logs', { params });
    return response.data;
  },

  // Get delivery tracking
  getDeliveryTracking: async (orderId) => {
    const response = await api.get(`/logistics/delivery-tracking/${orderId}`);
    return response.data;
  },

  // Optimize logistics
  optimizeLogistics: async (optimizationData) => {
    const response = await api.post('/logistics/optimize-logistics', optimizationData);
    return response.data;
  },
};

// Export default API instance for other uses
export default api;
