import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", res.data.access_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: { email: string; password: string; name: string; company?: string }) =>
    api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
  updateMe: (data: any) => api.put("/auth/me", data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/change-password", data),
};

export const leadsAPI = {
  list: (params?: any) => api.get("/leads", { params }),
  get: (id: number) => api.get(`/leads/${id}`),
  create: (data: any) => api.post("/leads", data),
  update: (id: number, data: any) => api.put(`/leads/${id}`, data),
  delete: (id: number) => api.delete(`/leads/${id}`),
  search: (data: any) => api.post("/leads/search", data),
  enrich: (id: number) => api.post(`/leads/${id}/enrich`),
  qualifyAI: (id: number) => api.post(`/leads/${id}/qualify-ai`),
  pipeline: () => api.get("/leads/pipeline/stats"),
  aiFind: (data: any) => api.post("/leads/ai-find", data),
};

export const campaignsAPI = {
  list: (params?: any) => api.get("/campaigns", { params }),
  get: (id: number) => api.get(`/campaigns/${id}`),
  create: (data: any) => api.post("/campaigns", data),
  update: (id: number, data: any) => api.put(`/campaigns/${id}`, data),
  delete: (id: number) => api.delete(`/campaigns/${id}`),
  launch: (id: number) => api.post(`/campaigns/${id}/launch`),
  pause: (id: number) => api.post(`/campaigns/${id}/pause`),
  getSequences: (id: number) => api.get(`/campaigns/${id}/sequences`),
  createSequence: (id: number, data: any) => api.post(`/campaigns/${id}/sequences`, data),
};

export const analyticsAPI = {
  dashboard: () => api.get("/analytics/dashboard"),
  pipeline: () => api.get("/analytics/pipeline"),
  daily: (days?: number) => api.get("/analytics/daily", { params: { days } }),
  mrr: (months?: number) => api.get("/analytics/mrr", { params: { months } }),
  channels: () => api.get("/analytics/channels"),
  locations: () => api.get("/analytics/leads-by-location"),
  activity: (limit?: number) => api.get("/analytics/activity", { params: { limit } }),
};

export const clientsAPI = {
  list: (params?: any) => api.get("/clients", { params }),
  get: (id: number) => api.get(`/clients/${id}`),
  create: (data: any) => api.post("/clients", data),
  update: (id: number, data: any) => api.put(`/clients/${id}`, data),
  delete: (id: number) => api.delete(`/clients/${id}`),
};

export const integrationsAPI = {
  list: () => api.get("/integrations"),
  connect: (provider: string, credentials: any, config?: any) =>
    api.post(`/integrations/${provider}`, { ...credentials, ...config }),
  disconnect: (id: number) => api.delete(`/integrations/${id}`),
  sync: (id: number) => api.post(`/integrations/${id}/sync`),
};
