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
  Factory,
  ChevronDown,
  Bell,
  Menu,
  Search,
  Settings,
  BookOpen,
  BarChart3,
  Truck
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
    { name: 'Order Creation', href: '/order-creation', icon: Package },
    { name: 'FMCG Order Aggregation', href: '/order-aggregation', icon: Factory },
  ];

  // Collapsible sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  // Mock notifications
  const notifications = [
    { id: 1, message: "New order ORD-10001 received", time: "10 minutes ago" },
    { id: 2, message: "Trip planning optimizations complete", time: "1 hour ago" },
    { id: 3, message: "System maintenance scheduled for tomorrow", time: "3 hours ago" }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="px-4 sm:px-6 lg:px-8 flex h-16 items-center justify-between">
          <div className="flex items-center">
            <button
              type="button"
              className="md:hidden p-2 text-gray-500 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="flex items-center">
              <Building className="h-8 w-8 text-blue-600 flex-shrink-0" />
              <h1 className="ml-3 font-bold text-xl text-gray-900 hidden md:block">FMCG Order Planner Agent</h1>
            </div>
          </div>
          
          <div className="hidden md:block mx-4 flex-1 max-w-md">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search orders, trips, etc."
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <div className="relative">
              <button
                className="p-1 text-gray-500 hover:text-blue-600 focus:outline-none"
                onClick={() => setNotificationsOpen(!notificationsOpen)}
              >
                <Bell className="h-6 w-6" />
                <span className="absolute top-0 right-0 block h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white"></span>
              </button>
              
              {notificationsOpen && (
                <div className="origin-top-right absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="py-1 divide-y divide-gray-200">
                    <div className="px-4 py-3">
                      <p className="text-sm font-medium text-gray-900">Notifications</p>
                    </div>
                    {notifications.map((notification) => (
                      <div key={notification.id} className="px-4 py-3 hover:bg-gray-50 cursor-pointer">
                        <p className="text-sm text-gray-800">{notification.message}</p>
                        <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                      </div>
                    ))}
                    <div className="px-4 py-2 text-center">
                      <button className="text-sm text-blue-600 font-medium hover:text-blue-500">
                        View all notifications
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* User menu */}
            <div className="relative">
              <button
                className="flex items-center text-sm focus:outline-none"
                onClick={() => setProfileOpen(!profileOpen)}
              >
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
                  {user?.contact_person?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </div>
                <span className="hidden md:flex ml-2 items-center">
                  <span className="mr-1 text-sm font-medium text-gray-700">
                    {user?.contact_person || user?.email}
                  </span>
                  <ChevronDown className="h-4 w-4 text-gray-500" />
                </span>
              </button>
              
              {profileOpen && (
                <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="py-1">
                    <Link to="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <div className="flex items-center">
                        <User className="h-4 w-4 mr-2" />
                        Your Profile
                      </div>
                    </Link>
                    <Link to="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <div className="flex items-center">
                        <Settings className="h-4 w-4 mr-2" />
                        Settings
                      </div>
                    </Link>
                    <Link to="/help" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <div className="flex items-center">
                        <BookOpen className="h-4 w-4 mr-2" />
                        Help & Documentation
                      </div>
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <div className="flex items-center">
                        <LogOut className="h-4 w-4 mr-2" />
                        Logout
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar for desktop */}
        <div className={`hidden md:flex transition-all duration-200 bg-white border-r border-gray-200 shadow-sm ${sidebarOpen ? 'w-64' : 'w-20'} flex-col`}>
          <div className="flex-1 flex flex-col overflow-y-auto pt-3">
            <div className="flex items-center justify-end px-4">
              <button
                className="text-gray-500 hover:text-blue-600 focus:outline-none"
                onClick={() => setSidebarOpen((open) => !open)}
                title={sidebarOpen ? 'Collapse' : 'Expand'}
              >
                {sidebarOpen ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
                )}
              </button>
            </div>
            <nav className="flex-1 py-4 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-4 py-2.5 mx-3 my-1 text-sm font-medium rounded-lg transition-colors ${
                    isActive(item.href)
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                  title={item.name}
                >
                  <item.icon className={`${sidebarOpen ? 'mr-3' : 'mx-auto'} h-5 w-5 flex-shrink-0 ${isActive(item.href) ? 'text-blue-600' : 'text-gray-500'}`} />
                  {sidebarOpen && <span>{item.name}</span>}
                </Link>
              ))}
            </nav>
          </div>
          <div className="px-3 py-4 border-t border-gray-200">
            <div className="bg-blue-50 text-blue-700 px-3 py-3 rounded-lg">
              <p className={`text-xs font-medium ${sidebarOpen ? 'block' : 'hidden'}`}>System Status</p>
              <div className="flex items-center mt-1">
                <div className="h-2.5 w-2.5 rounded-full bg-green-500 mr-2"></div>
                <p className={`text-xs ${sidebarOpen ? 'block' : 'hidden'}`}>All systems operational</p>
                {!sidebarOpen && <div className="h-2.5 w-2.5 rounded-full bg-green-500 mx-auto"></div>}
              </div>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 md:hidden">
            {/* Background overlay */}
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setMobileMenuOpen(false)}></div>
            
            {/* Sidebar */}
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
              <div className="px-4 pt-5 pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Building className="h-8 w-8 text-blue-600" />
                    <h1 className="ml-3 text-xl font-bold text-gray-900">FMCG Order Planner Agent</h1>
                  </div>
                  <button
                    className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <span className="sr-only">Close sidebar</span>
                    <svg className="h-6 w-6 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="mt-5">
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Search"
                    />
                  </div>
                </div>
                <nav className="mt-5 space-y-1">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-4 py-2 text-base font-medium rounded-md ${
                        isActive(item.href)
                          ? 'bg-blue-50 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <item.icon className={`mr-4 h-6 w-6 flex-shrink-0 ${isActive(item.href) ? 'text-blue-600' : 'text-gray-500'}`} />
                      {item.name}
                    </Link>
                  ))}
                </nav>
              </div>
              <div className="pt-4 pb-3 border-t border-gray-200">
                <div className="flex items-center px-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white text-lg font-semibold">
                      {user?.contact_person?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </div>
                  </div>
                  <div className="ml-3">
                    <div className="text-base font-medium text-gray-800">{user?.contact_person || user?.email}</div>
                    <div className="text-sm font-medium text-gray-500">{user?.role || 'User'}</div>
                  </div>
                </div>
                <div className="mt-3 space-y-1 px-2">
                  <Link
                    to="/profile"
                    className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Your Profile
                  </Link>
                  <Link
                    to="/settings"
                    className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Settings
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setMobileMenuOpen(false);
                    }}
                    className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
