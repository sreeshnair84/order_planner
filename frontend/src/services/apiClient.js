import axios from 'axios';

const API_BASE_URL =  'https://dispatchplannerapp.wonderfultree-66eac7c6.eastus.azurecontainerapps.io';

// Create axios instance with default config
const api = axios.create({
  baseURL: `${API_BASE_URL.replace('/api', '')}/api/`,  // Note the trailing slash
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 30 seconds timeout
  // Configure axios to follow redirects automatically but with specific settings
  maxRedirects: 5,
  // Ensure we handle 307 redirects properly
  validateStatus: function (status) {
    return status >= 200 && status < 300; // default
  }
});

// Request interceptor to add auth token and log requests
api.interceptors.request.use(
  (config) => {
    // Log the full URL being requested for debugging
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Bearer token added to request');
    } else {
      console.warn('⚠️ No access token found in localStorage');
    }
    
    // Ensure HTTPS URLs
    if (config.baseURL && config.baseURL.startsWith('http://') && !config.baseURL.includes('localhost')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
      console.log(`🔒 Converted to HTTPS: ${config.baseURL}`);
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and redirects
api.interceptors.response.use(
  (response) => {
    // Log successful responses for debugging
    console.log(`API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Log error details including redirect information
    if (error.response) {
      console.error(`API Error: ${error.response.status} ${error.config.method?.toUpperCase()} ${error.config.url}`);
      console.error('Response headers:', error.response.headers);
      
      // Handle 307 Temporary Redirect specifically
      if (error.response.status === 307) {
        const location = error.response.headers.location;
        console.warn(`Received 307 redirect to: ${location}`);
        
        if (location && !originalRequest._redirect) {
          originalRequest._redirect = true;
          // Update the URL to the redirect location
          const redirectUrl = new URL(location);
          
          // Ensure redirect is HTTPS for production URLs
          if (redirectUrl.hostname.includes('azurecontainerapps.io') && redirectUrl.protocol === 'http:') {
            redirectUrl.protocol = 'https:';
            console.log(`🔒 Converted redirect to HTTPS: ${redirectUrl.href}`);
          }
          
          originalRequest.url = redirectUrl.pathname + redirectUrl.search;
          originalRequest.baseURL = `${redirectUrl.protocol}//${redirectUrl.host}`;
          
          // Preserve the Authorization header for the redirect
          const token = localStorage.getItem('access_token');
          if (token && !originalRequest.headers.Authorization) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            console.log('✅ Re-added bearer token to redirect request');
          }
          
          console.log(`Following redirect to: ${originalRequest.baseURL}${originalRequest.url}`);
          return api(originalRequest);
        }
      }
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Create a new axios instance for refresh to avoid circular dependency
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          });

          const { access_token, refresh_token } = refreshResponse.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Export the base URL for debugging purposes
export const getApiBaseUrl = () => {
  const baseUrl = API_BASE_URL.replace('/api', '');
  return `${baseUrl}/api`;
};

// Export function to get current environment configuration
export const getApiConfig = () => {
  return {
    API_BASE_URL,
    processedBaseURL: `${API_BASE_URL.replace('/api', '')}/api`,
    environment: process.env.NODE_ENV,
    reactAppApiUrl: process.env.REACT_APP_API_URL
  };
};
