import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления токена
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: (login, password) => {
    const formData = new URLSearchParams();
    formData.append('username', login);
    formData.append('password', password);
    
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  
  getCurrentUser: () => api.get('/auth/me'),
  
  register: (userData) => api.post('/auth/register', userData),
};

export const userService = {
  getAllUsers: () => api.get('/users'),
  getUser: (id) => api.get(`/users/${id}`),
  updateUser: (id, data) => api.put(`/users/${id}`, data),
  deleteUser: (id) => api.delete(`/users/${id}`),
  blockUser: (id) => api.post(`/users/${id}/block`),
  unblockUser: (id) => api.post(`/users/${id}/unblock`),
  changePassword: (id, newPassword) => api.post(`/users/${id}/change-password?new_password=${newPassword}`),
};

export const checkService = {
  createCheck: (data) => api.post('/checks', data),
  getChecks: () => api.get('/checks'),
  getCheck: (id) => api.get(`/checks/${id}`),
  uploadFiles: (id, files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return api.post(`/checks/${id}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getNTDDocuments: () => api.get('/checks/ntd'),
  addNTDDocument: (data) => api.post('/checks/ntd', data),
  updateNTDDocument: (id, data) => api.put(`/checks/ntd/${id}`, data),
  deleteNTDDocument: (id) => api.delete(`/checks/ntd/${id}`),
};

export const reportService = {
  generateReport: (checkId, format) => api.post('/reports/generate', { check_id: checkId, format }),
  getCableWedomost: (checkId) => api.get(`/reports/${checkId}/ведомость-кабеля`),
  getEquipmentWedomost: (checkId) => api.get(`/reports/${checkId}/ведомость-оборудования`),
};

export default api;
