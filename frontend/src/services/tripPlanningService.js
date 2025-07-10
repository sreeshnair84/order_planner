import api from './apiClient';

export const tripPlanningService = {
  // Get available orders for trip planning
  async getAvailableOrders() {
    try {
      const response = await api.get('/trips/orders');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get manufacturing locations
  async getManufacturingLocations() {
    try {
      const response = await api.get('/trips/manufacturing-locations');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get available trucks
  async getTrucks(locationId) {
    try {
      const response = await api.get(`/trips/trucks?location_id=${locationId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Optimize trip routes
  async optimizeRoutes(optimizationData) {
    try {
      const response = await api.post('/trips/optimize-routes', optimizationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Optimize SKU consolidation
  async optimizeSKUs(consolidationData) {
    try {
      const response = await api.post('/trips/optimize-skus', consolidationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get route details
  async getRouteDetails(routeId) {
    try {
      const response = await api.get(`/trips/routes/${routeId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get trip analytics
  async getTripAnalytics(params) {
    try {
      const response = await api.get('/trips/analytics', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Assign truck to route
  async assignTruck(routeId, truckId) {
    try {
      const response = await api.post(`/trips/routes/${routeId}/assign-truck`, { truck_id: truckId });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Resolve time conflicts
  async resolveTimeConflict(conflictData) {
    try {
      const response = await api.post('/trips/resolve-time-conflict', conflictData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Reorder route
  async reorderRoute(routeId, reorderData) {
    try {
      const response = await api.post(`/trips/routes/${routeId}/reorder`, reorderData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Real-time route optimization
  async optimizeRouteRealTime(routeId, optimizationData) {
    try {
      const response = await api.post(`/trips/routes/${routeId}/optimize-realtime`, optimizationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};

export const logisticsService = {
  // Get performance metrics
  async getPerformanceMetrics(params) {
    try {
      const response = await api.get('/logistics/performance-metrics', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get capacity planning data
  async getCapacityPlanning(params) {
    try {
      const response = await api.get('/logistics/capacity-planning', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get real-time tracking
  async getRealTimeTracking(params) {
    try {
      const response = await api.get('/logistics/real-time-tracking', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get optimization logs
  async getOptimizationLogs(params) {
    try {
      const response = await api.get('/logistics/optimization-logs', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get delivery tracking
  async getDeliveryTracking(orderId) {
    try {
      const response = await api.get(`/logistics/delivery-tracking/${orderId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Optimize logistics
  async optimizeLogistics(optimizationData) {
    try {
      const response = await api.post('/logistics/optimize-logistics', optimizationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};

// Legacy exports for backward compatibility
export const tripPlanningAPI = tripPlanningService;
export const logisticsAPI = logisticsService;

export default api;
