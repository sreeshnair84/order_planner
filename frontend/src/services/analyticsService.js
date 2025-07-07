import api from './apiClient';

export const analyticsService = {
  // Dashboard statistics
  async getDashboardStats(dateRange = 30) {
    try {
      const response = await api.get('/analytics/dashboard/stats', {
        params: { date_range: dateRange }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Order status distribution for charts
  async getOrderStatusDistribution(dateRange = 30) {
    try {
      const response = await api.get('/analytics/status-distribution', {
        params: { date_range: dateRange }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Monthly trends data
  async getMonthlyTrends(months = 6) {
    try {
      const response = await api.get('/analytics/monthly-trends', {
        params: { months }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Performance metrics
  async getPerformanceMetrics(dateRange = 30) {
    try {
      const response = await api.get('/analytics/performance-metrics', {
        params: { date_range: dateRange }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Recent activities
  async getRecentActivities(limit = 10) {
    try {
      const response = await api.get('/analytics/recent-activities', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Comprehensive analytics (all data in one call)
  async getComprehensiveAnalytics(dateRange = 30) {
    try {
      const response = await api.get('/analytics/comprehensive', {
        params: { date_range: dateRange }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Fleet metrics
  async getFleetMetrics() {
    try {
      const response = await api.get('/analytics/fleet/metrics');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Delivery performance trends
  async getDeliveryPerformance(dateRange = 30) {
    try {
      const response = await api.get('/analytics/delivery-performance', {
        params: { date_range: dateRange }
      });
      return response.data;
    } catch (error) {
      console.error('Delivery performance API not available, using fallback data:', error);
      // Return empty array if API doesn't exist - UI will handle gracefully
      return [];
    }
  },

  // Order aggregation data
  async getOrderAggregation(groupBy = 'category', dateRange = 30) {
    try {
      const response = await api.get('/analytics/order-aggregation', {
        params: { 
          group_by: groupBy,
          date_range: dateRange 
        }
      });
      return response.data;
    } catch (error) {
      console.error('Order aggregation API not available, using fallback data:', error);
      // Return empty array if API doesn't exist - UI will handle gracefully
      return [];
    }
  },

  // System notifications
  async getSystemNotifications() {
    try {
      const response = await api.get('/analytics/notifications');
      return response.data;
    } catch (error) {
      console.error('System notifications API not available, using fallback data:', error);
      // Return empty array if API doesn't exist - UI will handle gracefully
      return [];
    }
  }
};
