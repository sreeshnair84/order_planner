import api from './apiClient';

export const managementService = {
  // Retailer management
  async getRetailers(params = {}) {
    try {
      const response = await api.get('/management/retailers', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async createRetailer(retailerData) {
    try {
      const response = await api.post('/management/retailers', retailerData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async updateRetailer(retailerId, retailerData) {
    try {
      const response = await api.put(`/management/retailers/${retailerId}`, retailerData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deleteRetailer(retailerId) {
    try {
      const response = await api.delete(`/management/retailers/${retailerId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Manufacturer management
  async getManufacturers(params = {}) {
    try {
      const response = await api.get('/manufacturers', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getManufacturersDropdown() {
    try {
      const response = await api.get('/management/manufacturers/dropdown');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async createManufacturer(manufacturerData) {
    try {
      const response = await api.post('/manufacturers', manufacturerData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async updateManufacturer(manufacturerId, manufacturerData) {
    try {
      const response = await api.put(`/manufacturers/${manufacturerId}`, manufacturerData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deleteManufacturer(manufacturerId) {
    try {
      const response = await api.delete(`/manufacturers/${manufacturerId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getManufacturerOrders(manufacturerId) {
    try {
      const response = await api.get(`/manufacturers/${manufacturerId}/orders`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async assignRetailerToManufacturer(manufacturerId, retailerId) {
    try {
      const response = await api.post(`/manufacturers/${manufacturerId}/assign-retailer/${retailerId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async unassignRetailerFromManufacturer(manufacturerId, retailerId) {
    try {
      const response = await api.delete(`/manufacturers/${manufacturerId}/unassign-retailer/${retailerId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Route management
  async getRoutes(params = {}) {
    try {
      const response = await api.get('/management/routes', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async createRoute(routeData) {
    try {
      const response = await api.post('/management/routes', routeData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async updateRoute(routeId, routeData) {
    try {
      const response = await api.put(`/management/routes/${routeId}`, routeData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deleteRoute(routeId) {
    try {
      const response = await api.delete(`/management/routes/${routeId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};
