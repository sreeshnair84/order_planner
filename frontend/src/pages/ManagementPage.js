import React, { useState } from 'react';
import Layout from '../components/common/Layout';
import RetailerManagement from '../components/management/RetailerManagement';
import {
  Building,
  Users,
  MapPin,
  Package,
  Settings,
  TrendingUp,
  Database,
  Truck,
  Factory
} from 'lucide-react';

const ManagementPage = () => {
  const [activeTab, setActiveTab] = useState('retailers');

  const managementTabs = [
    {
      id: 'retailers',
      name: 'Retailers',
      icon: Building,
      description: 'Manage retail partners and their information',
      component: <RetailerManagement />
    },
    {
      id: 'manufacturers',
      name: 'Manufacturers',
      icon: Factory,
      description: 'Manage manufacturing partners and locations',
      component: <div className="p-6 text-center text-gray-500">Manufacturers management coming soon...</div>
    },
    {
      id: 'routes',
      name: 'Routes',
      icon: MapPin,
      description: 'Define and manage delivery routes',
      component: <div className="p-6 text-center text-gray-500">Route management coming soon...</div>
    },
    {
      id: 'sku',
      name: 'SKU Items',
      icon: Package,
      description: 'Manage product catalog and SKU information',
      component: <div className="p-6 text-center text-gray-500">SKU management coming soon...</div>
    },
    {
      id: 'trucks',
      name: 'Fleet',
      icon: Truck,
      description: 'Manage delivery fleet and truck information',
      component: <div className="p-6 text-center text-gray-500">Fleet management coming soon...</div>
    },
    {
      id: 'users',
      name: 'Users',
      icon: Users,
      description: 'Manage system users and permissions',
      component: <div className="p-6 text-center text-gray-500">User management coming soon...</div>
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: Settings,
      description: 'System configuration and preferences',
      component: <div className="p-6 text-center text-gray-500">Settings coming soon...</div>
    },
    {
      id: 'analytics',
      name: 'Analytics',
      icon: TrendingUp,
      description: 'Management analytics and reporting',
      component: <div className="p-6 text-center text-gray-500">Analytics coming soon...</div>
    }
  ];

  const activeTabData = managementTabs.find(tab => tab.id === activeTab);

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Management</h1>
            <p className="mt-2 text-sm text-gray-700">
              Manage your business entities, partners, and system configuration.
            </p>
          </div>
        </div>

        {/* Management Overview Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-blue-500">
                  <Building className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Active Retailers</dt>
                  <dd className="text-lg font-medium text-gray-900">12</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-green-500">
                  <Factory className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Manufacturers</dt>
                  <dd className="text-lg font-medium text-gray-900">5</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-purple-500">
                  <MapPin className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Delivery Routes</dt>
                  <dd className="text-lg font-medium text-gray-900">28</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-2 rounded-lg bg-yellow-500">
                  <Package className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">SKU Items</dt>
                  <dd className="text-lg font-medium text-gray-900">1,247</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Management Tabs */}
        <div className="card">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {managementTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm`}
                >
                  <tab.icon
                    className={`${
                      activeTab === tab.id ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                    } -ml-0.5 mr-2 h-5 w-5`}
                  />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="mt-6">
            {activeTabData && (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900">{activeTabData.name}</h3>
                  <p className="mt-1 text-sm text-gray-500">{activeTabData.description}</p>
                </div>
                {activeTabData.component}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Quick Actions</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <Building className="h-5 w-5 mr-2 text-blue-600" />
              Add Retailer
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <Factory className="h-5 w-5 mr-2 text-green-600" />
              Add Manufacturer
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <MapPin className="h-5 w-5 mr-2 text-purple-600" />
              Define Route
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
              <Database className="h-5 w-5 mr-2 text-yellow-600" />
              Import Data
            </button>
          </div>
        </div>

        {/* System Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">System Status</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">Database</p>
                  <p className="text-xs text-green-600">Connected</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">API Services</p>
                  <p className="text-xs text-green-600">Online</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">Email Service</p>
                  <p className="text-xs text-green-600">Active</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ManagementPage;
