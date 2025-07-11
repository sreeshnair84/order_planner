import api from './apiClient';

export const orderProcessingService = {
  // Order processing unified
  async getOrderSummaryUnified(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/summary-unified`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getProcessingMethods() {
    try {
      const response = await api.get('/requestedorders/processing/methods');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async processOrderUnified(orderId, options = {}) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/process-unified`, options);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async processOrderStep(orderId, stepData) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/process-step`, stepData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async retryOrderStep(orderId, stepData) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/retry-step`, stepData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Order actions
  async correctMissingFields(orderId, corrections) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/correct-missing-fields`, { corrections });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async correctValidationErrors(orderId, corrections) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/correct-validation-errors`, { corrections });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async resendEmail(orderId, emailData) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/resend-email`, emailData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // User actions
  async getUserActions(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/user-actions`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async completeUserAction(orderId, actionData) {
    try {
      // Use FormData for file uploads
      const formData = new FormData();
      formData.append('orderId', orderId);
      formData.append('actionType', actionData.actionType);
      formData.append('data', JSON.stringify(actionData.data));
      
      if (actionData.files) {
        actionData.files.forEach((file, index) => {
          formData.append(`file_${index}`, file);
        });
      }

      const response = await api.post(`/requestedorders/${orderId}/complete-user-action`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async skipUserAction(orderId, actionId, params = {}) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/skip-user-action`, { actionId, ...params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deferUserAction(orderId, actionId, params = {}) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/defer-user-action`, { actionId, ...params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Order status and metrics
  async getOrderStatus(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/status`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderProcessingMetrics(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/processing-metrics`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getOrderNotifications(orderId) {
    try {
      const response = await api.get(`/requestedorders/${orderId}/notifications`);
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

  // Email management
  async approveEmail(orderId, emailId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/emails/${emailId}/approve`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async sendEmail(orderId, emailData) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/send-email`, emailData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async editEmail(orderId, emailId, emailData) {
    try {
      const response = await api.put(`/requestedorders/${orderId}/emails/${emailId}`, emailData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deleteEmail(orderId, emailId) {
    try {
      const response = await api.delete(`/requestedorders/${orderId}/emails/${emailId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Validation and reprocessing
  async validateOrder(orderId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/validate`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async generateEmail(orderId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/generate-email`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async parseFile(orderId) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/parse-file`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Order processing control
  async restartFromCheckpoint(orderId, checkpoint) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/restart-checkpoint`, { checkpoint });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async retriggerJob(orderId, jobType) {
    try {
      const endpoint = {
        'file_parsing': `/requestedorders/${orderId}/parse-file`,
        'validation': `/requestedorders/${orderId}/validate`,
        'email_generation': `/requestedorders/${orderId}/generate-email`,
        'full_processing': `/requestedorders/${orderId}/process`
      }[jobType];

      const response = await api.post(endpoint);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async executeQuickAction(orderId, action) {
    try {
      const response = await api.post(`/requestedorders/${orderId}/${action}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
