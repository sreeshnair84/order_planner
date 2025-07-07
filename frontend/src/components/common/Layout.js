import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Upload, 
  Package, 
  LogOut, 
  User,
  Building,
  MapPin,
  Mail,
  Factory
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Upload Order', href: '/upload', icon: Upload },
    { name: 'Track Orders', href: '/tracking', icon: Package },
    { name: 'Order Processing', href: '/order-processing', icon: Package },
    { name: 'Trip Planning', href: '/trip-planning', icon: MapPin },
    { name: 'Logistics', href: '/logistics', icon: Building },
    { name: 'Management', href: '/management', icon: User },
    { name: 'Manufacturers', href: '/manufacturers', icon: Factory },
    { name: 'Email Management', href: '/emails', icon: Mail },
  ];

  // Collapsible sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`transition-all duration-200 bg-white border-r border-gray-200 shadow-sm ${sidebarOpen ? 'w-56' : 'w-16'} flex flex-col`}>
        <div className="flex items-center justify-between h-16 px-4 border-b">
          <div className="flex items-center">
            <Building className="h-8 w-8 text-blue-600" />
            <span className={`ml-2 text-xl font-bold text-gray-900 transition-all duration-200 ${sidebarOpen ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'}`}>Order Manager</span>
          </div>
          <button
            className="ml-auto text-gray-500 hover:text-blue-600 focus:outline-none"
            onClick={() => setSidebarOpen((open) => !open)}
            title={sidebarOpen ? 'Collapse' : 'Expand'}
          >
            {sidebarOpen ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 12H5" /></svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" /></svg>
            )}
          </button>
        </div>
        <nav className="flex-1 py-4">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`w-full flex items-center px-4 py-2 my-1 rounded transition-colors text-left ${
                isActive(item.href)
                  ? 'bg-blue-100 text-blue-700 font-semibold'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title={item.name}
            >
              <item.icon className="h-4 w-4 mr-2" />
              <span className={`transition-all duration-200 ${sidebarOpen ? 'block' : 'hidden'}`}>{item.name}</span>
              {!sidebarOpen && (
                <span className="mx-auto w-2 h-2 rounded-full bg-blue-400" />
              )}
            </Link>
          ))}
        </nav>
        <div className="flex flex-col items-center mb-4">
          <div className={`flex items-center text-sm text-gray-700 ${sidebarOpen ? 'mt-2' : 'mt-4'}`}>
            <User className="h-4 w-4 mr-1" />
            <span className={`${sidebarOpen ? 'block' : 'hidden'}`}>{user?.contact_person || user?.email}</span>
          </div>
          <button
            onClick={handleLogout}
            className={`mt-2 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${sidebarOpen ? '' : 'justify-center'}`}
            title="Logout"
          >
            <LogOut className="h-4 w-4 mr-2" />
            <span className={`${sidebarOpen ? 'block' : 'hidden'}`}>Logout</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 w-full">
          <div className="px-4 py-6 sm:px-0">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
