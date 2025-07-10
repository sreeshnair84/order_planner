import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  Search,
  Filter,
  Navigation as RouteIcon,
  MapPin,
  Truck,
  Clock,
  Package,
  DollarSign,
  RefreshCw,
  X,
  Save
} from 'lucide-react';
import { managementService } from '../../services/managementService';

const RouteManagement = () => {
  const [routes, setRoutes] = useState([]);
  const [manufacturers, setManufacturers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingRoute, setEditingRoute] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(10);
  const [formData, setFormData] = useState({
    name: '',
    manufacturer_id: '',
    origin_city: '',
    origin_state: '',
    origin_country: '',
    destination_city: '',
    destination_state: '',
    destination_country: '',
    distance_km: '',
    estimated_transit_days: 3,
    transport_mode: 'truck',
    cost_per_km: 0,
    max_weight_kg: '',
    max_volume_m3: '',
    is_active: true,
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, [currentPage, selectedManufacturer, searchTerm, activeFilter]);

  useEffect(() => {
    loadManufacturers();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        per_page: perPage,
        active_only: activeFilter === 'active'
      };
      
      if (searchTerm) {
        params.search = searchTerm;
      }
      
      if (selectedManufacturer) {
        params.manufacturer_id = selectedManufacturer;
      }

      const data = await managementService.getRoutes(params);
      setRoutes(Array.isArray(data.routes) ? data.routes : []);
      setTotal(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / perPage));
    } catch (error) {
      console.error('Error loading routes:', error);
      setRoutes([]);
    } finally {
      setLoading(false);
    }
  };

  const loadManufacturers = async () => {
    try {
      const data = await managementService.getManufacturersDropdown();
      setManufacturers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading manufacturers:', error);
      setManufacturers([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const routeData = {
        ...formData,
        manufacturer_id: parseInt(formData.manufacturer_id),
        distance_km: formData.distance_km ? parseInt(formData.distance_km) : null,
        estimated_transit_days: parseInt(formData.estimated_transit_days),
        cost_per_km: parseInt(formData.cost_per_km),
        max_weight_kg: formData.max_weight_kg ? parseInt(formData.max_weight_kg) : null,
        max_volume_m3: formData.max_volume_m3 ? parseInt(formData.max_volume_m3) : null,
      };

      if (editingRoute) {
        await managementService.updateRoute(editingRoute.id, routeData);
      } else {
        await managementService.createRoute(routeData);
      }
      
      await loadData();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving route:', error);
      alert(`Error: ${error.detail || error.message || 'Failed to save route'}`);
    }
  };

  const handleEdit = (route) => {
    setEditingRoute(route);
    setFormData({
      name: route.name,
      manufacturer_id: route.manufacturer_id.toString(),
      origin_city: route.origin_city,
      origin_state: route.origin_state || '',
      origin_country: route.origin_country || '',
      destination_city: route.destination_city,
      destination_state: route.destination_state || '',
      destination_country: route.destination_country || '',
      distance_km: route.distance_km?.toString() || '',
      estimated_transit_days: route.estimated_transit_days,
      transport_mode: route.transport_mode,
      cost_per_km: route.cost_per_km,
      max_weight_kg: route.max_weight_kg?.toString() || '',
      max_volume_m3: route.max_volume_m3?.toString() || '',
      is_active: route.is_active,
      notes: route.notes || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (routeId) => {
    if (!window.confirm('Are you sure you want to delete this route?')) return;
    
    try {
      await managementService.deleteRoute(routeId);
      await loadData();
    } catch (error) {
      console.error('Error deleting route:', error);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingRoute(null);
    setFormData({
      name: '',
      manufacturer_id: '',
      origin_city: '',
      origin_state: '',
      origin_country: '',
      destination_city: '',
      destination_state: '',
      destination_country: '',
      distance_km: '',
      estimated_transit_days: 3,
      transport_mode: 'truck',
      cost_per_km: 0,
      max_weight_kg: '',
      max_volume_m3: '',
      is_active: true,
      notes: ''
    });
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const transportModes = [
    { value: 'truck', label: 'Truck' },
    { value: 'rail', label: 'Rail' },
    { value: 'air', label: 'Air' },
    { value: 'sea', label: 'Sea' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading routes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Route Management</h1>
              <p className="text-sm text-gray-600">Manage transportation routes</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                <Plus className="w-4 h-4" />
                <span>Add Route</span>
              </button>
              <button
                onClick={loadData}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search routes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={activeFilter}
                onChange={(e) => setActiveFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Routes</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Manufacturer:</span>
              <select
                value={selectedManufacturer}
                onChange={(e) => setSelectedManufacturer(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Manufacturers</option>
                {manufacturers.map(manufacturer => (
                  <option key={manufacturer.id} value={manufacturer.id}>
                    {manufacturer.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Routes List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Routes</h3>
              <span className="text-sm text-gray-500">{total} routes</span>
            </div>

            {routes.length === 0 ? (
              <div className="text-center py-12">
                <RouteIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No routes found.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {routes.map((route) => (
                  <div key={route.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-lg font-medium text-gray-900">{route.name}</h4>
                          <span className={`px-2 py-1 text-xs rounded ${
                            route.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {route.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-2">
                            <MapPin className="w-4 h-4" />
                            <span>{route.origin_city} → {route.destination_city}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Truck className="w-4 h-4" />
                            <span className="capitalize">{route.transport_mode}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Clock className="w-4 h-4" />
                            <span>{route.estimated_transit_days} days</span>
                          </div>
                          {route.distance_km && (
                            <div className="flex items-center space-x-2">
                              <RouteIcon className="w-4 h-4" />
                              <span>{route.distance_km} km</span>
                            </div>
                          )}
                          {route.cost_per_km > 0 && (
                            <div className="flex items-center space-x-2">
                              <DollarSign className="w-4 h-4" />
                              <span>${(route.cost_per_km / 100).toFixed(2)}/km</span>
                            </div>
                          )}
                          {route.max_weight_kg && (
                            <div className="flex items-center space-x-2">
                              <Package className="w-4 h-4" />
                              <span>Max {route.max_weight_kg}kg</span>
                            </div>
                          )}
                        </div>
                        
                        {route.manufacturer && (
                          <div className="mt-2 text-sm text-gray-500">
                            Manufacturer: {route.manufacturer.name}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleEdit(route)}
                          className="p-2 text-blue-500 hover:bg-blue-100 rounded"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(route.id)}
                          className="p-2 text-red-500 hover:bg-red-100 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex justify-center space-x-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-1 border rounded ${
                      currentPage === page 
                        ? 'bg-blue-500 text-white' 
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={handleCloseModal}></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <form onSubmit={handleSubmit}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {editingRoute ? 'Edit Route' : 'Add New Route'}
                    </h3>
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Route Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Manufacturer *
                      </label>
                      <select
                        required
                        value={formData.manufacturer_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, manufacturer_id: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">Select Manufacturer</option>
                        {manufacturers.map(manufacturer => (
                          <option key={manufacturer.id} value={manufacturer.id}>
                            {manufacturer.name} ({manufacturer.code})
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Origin City *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.origin_city}
                        onChange={(e) => setFormData(prev => ({ ...prev, origin_city: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Origin State
                      </label>
                      <input
                        type="text"
                        value={formData.origin_state}
                        onChange={(e) => setFormData(prev => ({ ...prev, origin_state: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Origin Country
                      </label>
                      <input
                        type="text"
                        value={formData.origin_country}
                        onChange={(e) => setFormData(prev => ({ ...prev, origin_country: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Destination City *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.destination_city}
                        onChange={(e) => setFormData(prev => ({ ...prev, destination_city: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Destination State
                      </label>
                      <input
                        type="text"
                        value={formData.destination_state}
                        onChange={(e) => setFormData(prev => ({ ...prev, destination_state: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Destination Country
                      </label>
                      <input
                        type="text"
                        value={formData.destination_country}
                        onChange={(e) => setFormData(prev => ({ ...prev, destination_country: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Distance (km)
                      </label>
                      <input
                        type="number"
                        value={formData.distance_km}
                        onChange={(e) => setFormData(prev => ({ ...prev, distance_km: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Transit Days
                      </label>
                      <input
                        type="number"
                        value={formData.estimated_transit_days}
                        onChange={(e) => setFormData(prev => ({ ...prev, estimated_transit_days: parseInt(e.target.value) || 3 }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Transport Mode
                      </label>
                      <select
                        value={formData.transport_mode}
                        onChange={(e) => setFormData(prev => ({ ...prev, transport_mode: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {transportModes.map(mode => (
                          <option key={mode.value} value={mode.value}>
                            {mode.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Cost per km (cents)
                      </label>
                      <input
                        type="number"
                        value={formData.cost_per_km}
                        onChange={(e) => setFormData(prev => ({ ...prev, cost_per_km: parseInt(e.target.value) || 0 }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Weight (kg)
                      </label>
                      <input
                        type="number"
                        value={formData.max_weight_kg}
                        onChange={(e) => setFormData(prev => ({ ...prev, max_weight_kg: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Volume (m³)
                      </label>
                      <input
                        type="number"
                        value={formData.max_volume_m3}
                        onChange={(e) => setFormData(prev => ({ ...prev, max_volume_m3: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Status
                      </label>
                      <select
                        value={formData.is_active}
                        onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.value === 'true' }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                      </select>
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Notes
                      </label>
                      <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {editingRoute ? 'Update' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RouteManagement;
