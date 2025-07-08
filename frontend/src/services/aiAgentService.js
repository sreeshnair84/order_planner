import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AIAgentService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle auth errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Create a new AI agent thread
  async createThread(orderId, message, autoStart = true) {
    const response = await this.api.post('/api/ai-agent/threads', {
      order_id: orderId,
      message: message,
      auto_start: autoStart
    });
    return response.data;
  }

  // Get thread state
  async getThreadState(threadId) {
    const response = await this.api.get(`/api/ai-agent/threads/${threadId}`);
    return response.data;
  }

  // Run agent on existing thread
  async runAgent(threadId) {
    const response = await this.api.post(`/api/ai-agent/threads/${threadId}/run`);
    return response.data;
  }

  // Add message to thread
  async addMessageToThread(threadId, message) {
    const response = await this.api.post(`/api/ai-agent/threads/${threadId}/messages`, {
      message: message
    });
    return response.data;
  }

  // Get all threads for an order
  async getOrderThreads(orderId) {
    const response = await this.api.get(`/api/ai-agent/orders/${orderId}/threads`);
    return response.data;
  }

  // Process order with AI (convenience method)
  async processOrderWithAI(orderId) {
    const response = await this.api.post(`/api/ai-agent/orders/${orderId}/process-with-ai`);
    return response.data;
  }

  // Get AI processing status
  async getAIProcessingStatus(orderId) {
    try {
      const threads = await this.getOrderThreads(orderId);
      const activeThreads = threads.data?.threads?.filter(
        thread => ['RUNNING', 'CREATED'].includes(thread.status)
      ) || [];
      
      return {
        isProcessing: activeThreads.length > 0,
        activeThreads: activeThreads,
        totalThreads: threads.data?.threads?.length || 0
      };
    } catch (error) {
      console.error('Failed to get AI processing status:', error);
      return {
        isProcessing: false,
        activeThreads: [],
        totalThreads: 0
      };
    }
  }
}

export const aiAgentService = new AIAgentService();
