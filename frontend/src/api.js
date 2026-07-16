import axios from 'axios';

// Update this with your deployed backend URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Resolves a relative image path into a full URL
export const getImageUrl = (path) => {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_URL}${path}`;
};

// Lead API
export const submitLead = async (data) => {
  const payload = {
    name: data.name || 'Visitor',
    company: data.company || 'Walk-in Visitor',
    email: data.email || '',
    phone: data.phone || '',
    requirement_type: data.requirement_type || 'General Inquiry',
    customer_type: data.customer_type || 'Other',
    other_customer_type: data.other_customer_type || '',
    message: data.message || '',
    source: data.source || 'web_form',
    image_url: data.image_url || null,
  };

  console.log('Submitting lead:', payload);
  const response = await api.post('/api/leads', payload);
  return response.data;
};

// Admin API
export const getLeads = async (filters = {}) => {
  const params = new URLSearchParams();
  Object.keys(filters).forEach(key => {
    if (filters[key]) params.append(key, filters[key]);
  });
  const response = await api.get(`/api/admin/leads?${params}`);
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/admin/stats');
  return response.data;
};

export const updateLeadStatus = async (id, status) => {
  const response = await api.patch(`/api/admin/leads/${id}/status`, { status });
  return response.data;
};

export const deleteLead = async (id) => {
  const response = await api.delete(`/api/admin/leads/${id}`);
  return response.data;
};

export const exportCSV = () => {
  window.open(`${API_URL}/api/admin/export/csv`, '_blank');
};

export const exportExcel = () => {
  window.open(`${API_URL}/api/admin/export/excel`, '_blank');
};

export default api;