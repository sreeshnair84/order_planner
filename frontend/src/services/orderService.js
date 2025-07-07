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

  // Enhanced order processing endpoints
  async getProcessingStatus(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/processing-status`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getProcessingSteps(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/processing-steps`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderEmails(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/emails`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getUserActions(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/user-actions`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async sendOrderEmail(orderId, emailData) {
    try {
      const response = await api.post(`/orders/${orderId}/send-email`, emailData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async approveEmail(orderId, emailId) {
    try {
      const response = await api.post(`/orders/${orderId}/emails/${emailId}/approve`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async correctMissingInfo(orderId, corrections) {
    try {
      const response = await api.post(`/orders/${orderId}/correct-info`, corrections);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async regenerateEmail(orderId, emailType = 'missing_info') {
    try {
      const response = await api.post(`/orders/${orderId}/regenerate-email`, { email_type: emailType });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async retryStep(orderId, stepId) {
    try {
      const response = await api.post(`/orders/${orderId}/retry-step`, { step: stepId });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getValidationSummary(orderId) {
    try {
      const response = await api.get(`/orders/${orderId}/validation-summary`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
