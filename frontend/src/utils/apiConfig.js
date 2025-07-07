const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getApiUrl = (path) => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};

export const apiConfig = {
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

export default {
  getApiUrl,
  apiConfig,
  API_BASE_URL
};
