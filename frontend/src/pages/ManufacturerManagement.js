import React, { useState, useEffect } from 'react';
import { managementService } from '../services/managementService';
import { Plus, Edit, Trash2, Users, Package, Search, Eye, Link, Unlink } from 'lucide-react';

const ManufacturerManagement = () => {
  const [manufacturers, setManufacturers] = useState([]);
  const [retailers, setRetailers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingManufacturer, setEditingManufacturer] = useState(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedManufacturer, setSelectedManufacturer] = useState(null);
  const [showOrdersModal, setShowOrdersModal] = useState(false);
  const [manufacturerOrders, setManufacturerOrders] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    code: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: '',
    notes: '',
    lead_time_days: 7,
    min_order_value: 0,
    preferred_payment_terms: ''
  });

  useEffect(() => {
    fetchManufacturers();
    fetchRetailers();
  }, []);

  const fetchManufacturers = async () => {
    try {
      const data = await managementService.getManufacturers();
      setManufacturers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching manufacturers:', error);
      setManufacturers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchRetailers = async () => {
    try {
      const data = await managementService.getRetailers();
      const retailersData = data.retailers || data;
      setRetailers(Array.isArray(retailersData) ? retailersData : []);
    } catch (error) {
      console.error('Error fetching retailers:', error);
      setRetailers([]);
    }
  };

  const fetchManufacturerOrders = async (manufacturerId) => {
    try {
      const data = await managementService.getManufacturerOrders(manufacturerId);
      setManufacturerOrders(data);
    } catch (error) {
      console.error('Error fetching manufacturer orders:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingManufacturer) {
        await managementService.updateManufacturer(editingManufacturer.id, formData);
      } else {
        await managementService.createManufacturer(formData);
      }
      
      fetchManufacturers();
      setShowForm(false);
      setEditingManufacturer(null);
      setFormData({
        name: '',
        code: '',
        contact_email: '',
        contact_phone: '',
        address: '',
        city: '',
        state: '',
        zip_code: '',
        country: '',
        notes: '',
        lead_time_days: 7,
        min_order_value: 0,
        preferred_payment_terms: ''
      });
    } catch (error) {
      console.error('Error saving manufacturer:', error);
    }
  };

  const handleEdit = (manufacturer) => {
    setEditingManufacturer(manufacturer);
    setFormData({
      name: manufacturer.name || '',
      code: manufacturer.code || '',
      contact_email: manufacturer.contact_email || '',
      contact_phone: manufacturer.contact_phone || '',
      address: manufacturer.address || '',
      city: manufacturer.city || '',
      state: manufacturer.state || '',
      zip_code: manufacturer.zip_code || '',
      country: manufacturer.country || '',
      notes: manufacturer.notes || '',
      lead_time_days: manufacturer.lead_time_days || 7,
      min_order_value: manufacturer.min_order_value || 0,
      preferred_payment_terms: manufacturer.preferred_payment_terms || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this manufacturer?')) {
      try {
        await managementService.deleteManufacturer(id);
        fetchManufacturers();
      } catch (error) {
        console.error('Error deleting manufacturer:', error);
      }
    }
  };

  const handleAssignRetailer = async (manufacturerId, retailerId) => {
    try {
      await managementService.assignRetailerToManufacturer(manufacturerId, retailerId);
      fetchManufacturers();
      setShowAssignModal(false);
    } catch (error) {
      console.error('Error assigning retailer:', error);
    }
  };

  const handleUnassignRetailer = async (manufacturerId, retailerId) => {
    try {
      await managementService.unassignRetailerFromManufacturer(manufacturerId, retailerId);
      fetchManufacturers();
    } catch (error) {
      console.error('Error unassigning retailer:', error);
    }
  };

  const showOrders = (manufacturer) => {
    setSelectedManufacturer(manufacturer);
    fetchManufacturerOrders(manufacturer.id);
    setShowOrdersModal(true);
  };

  const filteredManufacturers = manufacturers.filter(manufacturer =>
    manufacturer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    manufacturer.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Manufacturer Management</h1>
        <p className="text-gray-600">Manage manufacturers and their retailer assignments</p>
      </div>

      {/* Search and Add Button */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search manufacturers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Manufacturer
        </button>
      </div>

      {/* Manufacturers Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Manufacturer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Stats
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredManufacturers.map((manufacturer) => (
              <tr key={manufacturer.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{manufacturer.name}</div>
                    <div className="text-sm text-gray-500">Code: {manufacturer.code}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{manufacturer.contact_email}</div>
                  <div className="text-sm text-gray-500">{manufacturer.contact_phone}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{manufacturer.city}</div>
                  <div className="text-sm text-gray-500">{manufacturer.state}, {manufacturer.country}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-600">{manufacturer.retailer_count}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Package className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-600">{manufacturer.active_orders}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <button
                    onClick={() => handleEdit(manufacturer)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedManufacturer(manufacturer);
                      setShowAssignModal(true);
                    }}
                    className="text-green-600 hover:text-green-900"
                  >
                    <Link className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => showOrders(manufacturer)}
                    className="text-purple-600 hover:text-purple-900"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(manufacturer.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">
                {editingManufacturer ? 'Edit Manufacturer' : 'Add New Manufacturer'}
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Code *
                    </label>
                    <input
                      type="text"
                      value={formData.code}
                      onChange={(e) => setFormData({...formData, code: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Email *
                    </label>
                    <input
                      type="email"
                      value={formData.contact_email}
                      onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.contact_phone}
                      onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Address
                    </label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => setFormData({...formData, address: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      City
                    </label>
                    <input
                      type="text"
                      value={formData.city}
                      onChange={(e) => setFormData({...formData, city: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      State
                    </label>
                    <input
                      type="text"
                      value={formData.state}
                      onChange={(e) => setFormData({...formData, state: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ZIP Code
                    </label>
                    <input
                      type="text"
                      value={formData.zip_code}
                      onChange={(e) => setFormData({...formData, zip_code: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Country
                    </label>
                    <input
                      type="text"
                      value={formData.country}
                      onChange={(e) => setFormData({...formData, country: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Lead Time (days)
                    </label>
                    <input
                      type="number"
                      value={formData.lead_time_days}
                      onChange={(e) => setFormData({...formData, lead_time_days: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="1"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Order Value
                    </label>
                    <input
                      type="number"
                      value={formData.min_order_value}
                      onChange={(e) => setFormData({...formData, min_order_value: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0"
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Payment Terms
                    </label>
                    <input
                      type="text"
                      value={formData.preferred_payment_terms}
                      onChange={(e) => setFormData({...formData, preferred_payment_terms: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g., Net 30, COD, etc."
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({...formData, notes: e.target.value})}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setEditingManufacturer(null);
                    }}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    {editingManufacturer ? 'Update' : 'Create'} Manufacturer
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Assign Retailer Modal */}
      {showAssignModal && selectedManufacturer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">
                Manage Retailer Assignments - {selectedManufacturer.name}
              </h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2">Assign New Retailer</h3>
                  <div className="space-y-2">
                    {retailers.filter(r => !selectedManufacturer.retailers?.some(mr => mr.id === r.id)).map(retailer => (
                      <div key={retailer.id} className="flex items-center justify-between p-2 border rounded">
                        <span>{retailer.name}</span>
                        <button
                          onClick={() => handleAssignRetailer(selectedManufacturer.id, retailer.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          <Link className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Currently Assigned Retailers</h3>
                  <div className="space-y-2">
                    {selectedManufacturer.retailers?.map(retailer => (
                      <div key={retailer.id} className="flex items-center justify-between p-2 border rounded bg-green-50">
                        <span>{retailer.name}</span>
                        <button
                          onClick={() => handleUnassignRetailer(selectedManufacturer.id, retailer.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Unlink className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Orders Modal */}
      {showOrdersModal && selectedManufacturer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">
                Orders for {selectedManufacturer.name}
              </h2>
              
              {manufacturerOrders.length === 0 ? (
                <p className="text-gray-500">No orders found for this manufacturer.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Order
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Retailer
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Details
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {manufacturerOrders.map((order) => (
                        <tr key={order.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{order.order_number}</div>
                            <div className="text-sm text-gray-500">{new Date(order.created_at).toLocaleDateString()}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              order.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                              order.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' :
                              order.status === 'ERROR' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {order.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{order.retailer || 'N/A'}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">Qty: {order.total_quantity}</div>
                            <div className="text-sm text-gray-500">Total: ${order.total}</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setShowOrdersModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManufacturerManagement;
