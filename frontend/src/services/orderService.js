import api from './apiClient';

export const orderService = {
  async uploadOrder(file, metadata) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('priority', metadata.priority || 'NORMAL');
      if (metadata.special_instructions) {
        formData.append('special_instructions', metadata.special_instructions);
      }

      const response = await api.post('/orders/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrders(params = {}) {
    try {
      const response = await api.get('/orders', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrder(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderDetails(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/details`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async processOrder(orderId) {
    try {
      const response = await api.post(`/orders/${orderId}/process`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async cancelOrder(orderId) {
    try {
      const response = await api.delete(`/orders/${orderId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderTracking(orderId) {
    try {
      const response = await api.get(`/tracking/${orderId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getAllOrdersTracking() {
    try {
      const response = await api.get('/tracking');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async updateOrderStatus(orderId, statusData) {
    try {
      const response = await api.post(`/tracking/${orderId}/status`, statusData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
