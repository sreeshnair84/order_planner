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

      const response = await api.post('/requestedorders/upload', formData, {
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
      const response = await api.get('/requestedorders/all', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrder(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderDetails(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/details`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async processOrder(orderId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/process`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async cancelOrder(orderId) {
    try {
      const response = await api.delete(`/requestedorders/${orderId}`);
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

  async getEmailCommunications(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/emails`);
      return response.data;
    } catch (error) {
      // Fallback to empty array if endpoint doesn't exist yet
      console.warn('Email communications endpoint not available:', error.message);
      return { data: [] };
    }
  },

  async uploadCorrection(file, originalOrderId, correctionType, referenceEmailId) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('original_order_id', originalOrderId);
      formData.append('correction_type', correctionType);
      formData.append('reference_email_id', referenceEmailId);

      const response = await api.post('/requestedorders/upload-correction', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async downloadOriginalFile(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/download-original`, {
        responseType: 'blob',
      });
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
      const response = await api.get(`/requestedorders/${orderId}/processing-status`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getProcessingSteps(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/processing-steps`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderEmails(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/emails`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getUserActions(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/user-actions`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async sendOrderEmail(orderId, emailData) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/send-email`, emailData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async approveEmail(orderId, emailId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/emails/${emailId}/approve`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async correctMissingInfo(orderId, corrections) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/correct-info`, corrections);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async regenerateEmail(orderId, emailType = 'missing_info') {
    try {
      const response = await api.post(`/requestedorders/${orderId}/regenerate-email`, { email_type: emailType });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async retryStep(orderId, stepId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/retry-step`, { step: stepId });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getValidationSummary(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/validation-summary`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // New order processing methods
  async reprocessOrder(orderId, newOrderId = null) {
    try {
      const payload = newOrderId ? { new_order_id: newOrderId } : {};
      const response = await api.post(`/requestedorders/${orderId}/reprocess`, payload);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async correctOrder(orderId, corrections) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/correct`, corrections);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async downloadOrderReport(orderId, format = 'pdf') {
    try {
      const response = await api.get(`/requestedorders/${orderId}/download?format=${format}`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderSKUItems(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/sku-details`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async downloadOrderData(orderId, format = 'csv') {
    try {
      const response = await api.get(`/requestedorders/${orderId}/download?format=${format}`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
