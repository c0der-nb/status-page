import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5010/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.client.post('/auth/refresh', {}, {
                headers: {
                  Authorization: `Bearer ${refreshToken}`,
                },
              });

              const { access_token } = response.data;
              localStorage.setItem('access_token', access_token);

              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    return response.data;
  }

  async register(data: {
    email: string;
    username: string;
    password: string;
    organization_name: string;
    organization_slug?: string;
    first_name?: string;
    last_name?: string;
  }) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Organizations
  async getOrganizations() {
    const response = await this.client.get('/organizations');
    return response.data;
  }

  async getOrganizationUsers(orgId: string) {
    const response = await this.client.get(`/organizations/${orgId}/users`);
    return response.data;
  }

  async getOrganization(id: string) {
    const response = await this.client.get(`/organizations/${id}`);
    return response.data;
  }

  async createOrganization(data: { name: string; slug?: string; description?: string }) {
    const response = await this.client.post('/organizations', data);
    return response.data;
  }

  async updateOrganization(id: string, data: any) {
    const response = await this.client.put(`/organizations/${id}`, data);
    return response.data;
  }

  async getOrganizationMembers(id: string) {
    const response = await this.client.get(`/organizations/${id}/members`);
    return response.data;
  }

  async addOrganizationMember(orgId: string, email: string, role: string) {
    const response = await this.client.post(`/organizations/${orgId}/members`, { email, role });
    return response.data;
  }

  async updateMemberRole(orgId: string, userId: string, role: string) {
    const response = await this.client.put(`/organizations/${orgId}/members/${userId}`, { role });
    return response.data;
  }

  async removeOrganizationMember(orgId: string, userId: string) {
    const response = await this.client.delete(`/organizations/${orgId}/members/${userId}`);
    return response.data;
  }

  // Teams
  async getTeams(orgId: string) {
    const response = await this.client.get('/teams', { params: { org_id: orgId } });
    return response.data;
  }

  async getTeam(id: string) {
    const response = await this.client.get(`/teams/${id}`);
    return response.data;
  }

  async createTeam(data: { name: string; description?: string; organization_id: string }) {
    const response = await this.client.post('/teams', data);
    return response.data;
  }

  async updateTeam(id: string, data: any) {
    const response = await this.client.put(`/teams/${id}`, data);
    return response.data;
  }

  async deleteTeam(id: string) {
    const response = await this.client.delete(`/teams/${id}`);
    return response.data;
  }

  async getTeamMembers(teamId: string) {
    const response = await this.client.get(`/teams/${teamId}/members`);
    return response.data;
  }

  async addTeamMember(teamId: string, data: { user_id: string; role: string }) {
    const response = await this.client.post(`/teams/${teamId}/members`, data);
    return response.data;
  }

  async removeTeamMember(teamId: string, userId: string) {
    const response = await this.client.delete(`/teams/${teamId}/members/${userId}`);
    return response.data;
  }

  // Services
  async getServices(orgId: string) {
    const response = await this.client.get('/services', { params: { org_id: orgId } });
    return response.data;
  }

  async getService(id: string) {
    const response = await this.client.get(`/services/${id}`);
    return response.data;
  }

  async createService(data: {
    name: string;
    description?: string;
    organization_id: string;
    team_id?: string;
    status?: string;
    is_public?: boolean;
  }) {
    const response = await this.client.post('/services', data);
    return response.data;
  }

  async updateService(id: string, data: any) {
    const response = await this.client.put(`/services/${id}`, data);
    return response.data;
  }

  async deleteService(id: string) {
    const response = await this.client.delete(`/services/${id}`);
    return response.data;
  }

  async reorderServices(orgId: string, serviceIds: string[]) {
    const response = await this.client.post('/services/reorder', {
      organization_id: orgId,
      service_ids: serviceIds,
    });
    return response.data;
  }

  // Incidents
  async getIncidents(orgId: string, filters?: { status?: string; type?: string }) {
    const response = await this.client.get('/incidents', {
      params: { org_id: orgId, ...filters },
    });
    return response.data;
  }

  async getIncident(id: string) {
    const response = await this.client.get(`/incidents/${id}`);
    return response.data;
  }

  async createIncident(data: {
    title: string;
    description?: string;
    organization_id: string;
    status?: string;
    impact?: string;
    type?: string;
    service_ids?: string[];
    initial_message?: string;
    scheduled_start?: string;
    scheduled_end?: string;
  }) {
    const response = await this.client.post('/incidents', data);
    return response.data;
  }

  async updateIncident(id: string, data: any) {
    const response = await this.client.put(`/incidents/${id}`, data);
    return response.data;
  }

  async deleteIncident(id: string) {
    const response = await this.client.delete(`/incidents/${id}`);
    return response.data;
  }

  async addIncidentUpdate(incidentId: string, message: string, status?: string) {
    const response = await this.client.post(`/incidents/${incidentId}/updates`, { message, status });
    return response.data;
  }

  // Public status page
  async getPublicStatus(orgSlug: string) {
    const response = await this.client.get(`/public/status/${orgSlug}`);
    return response.data;
  }

  async getPublicIncident(orgSlug: string, incidentId: string) {
    const response = await this.client.get(`/public/status/${orgSlug}/incidents/${incidentId}`);
    return response.data;
  }

  async subscribeToUpdates(orgSlug: string, email: string) {
    const response = await this.client.post(`/public/status/${orgSlug}/subscribe`, { email });
    return response.data;
  }

  // User profile
  async updateProfile(data: any) {
    const response = await this.client.put('/users/profile', data);
    return response.data;
  }

  async changePassword(currentPassword: string, newPassword: string) {
    const response = await this.client.post('/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  }

  async searchUsers(query: string, orgId?: string) {
    const response = await this.client.get('/users/search', {
      params: { q: query, org_id: orgId },
    });
    return response.data;
  }
}

export default new ApiClient();
