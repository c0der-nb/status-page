import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import wsClient from '../api/websocket';
import { Service, Incident } from '../types';
import { format } from 'date-fns';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { currentOrg } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalServices: 0,
    operationalServices: 0,
    activeIncidents: 0,
    scheduledMaintenance: 0,
  });

  useEffect(() => {
    if (currentOrg) {
      loadDashboardData();
    }
  }, [currentOrg]);

  useEffect(() => {
    // Listen for real-time updates
    const handleServiceUpdate = (data: any) => {
      if (data.organization_id === currentOrg?.id) {
        loadServices();
      }
    };

    const handleIncidentUpdate = (data: any) => {
      if (data.organization_id === currentOrg?.id) {
        loadIncidents();
      }
    };

    wsClient.on('service_status_changed', handleServiceUpdate);
    wsClient.on('incident_created', handleIncidentUpdate);
    wsClient.on('incident_updated', handleIncidentUpdate);

    return () => {
      wsClient.off('service_status_changed', handleServiceUpdate);
      wsClient.off('incident_created', handleIncidentUpdate);
      wsClient.off('incident_updated', handleIncidentUpdate);
    };
  }, [currentOrg]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([loadServices(), loadIncidents()]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadServices = async () => {
    if (!currentOrg) return;
    
    try {
      const response = await apiClient.getServices(currentOrg.id);
      setServices(response.services);
      
      // Calculate stats
      const operational = response.services.filter((s: Service) => s.status === 'operational').length;
      setStats(prev => ({
        ...prev,
        totalServices: response.services.length,
        operationalServices: operational,
      }));
    } catch (error) {
      console.error('Failed to load services:', error);
    }
  };

  const loadIncidents = async () => {
    if (!currentOrg) return;
    
    try {
      const response = await apiClient.getIncidents(currentOrg.id);
      setIncidents(response.incidents);
      
      // Calculate stats
      const active = response.incidents.filter((i: Incident) => 
        ['investigating', 'identified', 'monitoring'].includes(i.status)
      ).length;
      
      const maintenance = response.incidents.filter((i: Incident) => 
        i.type === 'maintenance' && ['scheduled', 'in_progress'].includes(i.status)
      ).length;
      
      setStats(prev => ({
        ...prev,
        activeIncidents: active,
        scheduledMaintenance: maintenance,
      }));
    } catch (error) {
      console.error('Failed to load incidents:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'status-operational';
      case 'degraded':
        return 'status-degraded';
      case 'partial_outage':
        return 'status-partial-outage';
      case 'major_outage':
        return 'status-major-outage';
      case 'maintenance':
        return 'status-maintenance';
      default:
        return '';
    }
  };

  const getIncidentStatusColor = (status: string) => {
    switch (status) {
      case 'investigating':
        return 'status-major-outage';
      case 'identified':
        return 'status-partial-outage';
      case 'monitoring':
        return 'status-degraded';
      case 'resolved':
        return 'status-operational';
      default:
        return '';
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner spinner-lg"></div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="text-muted">Overview of your status page</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalServices}</div>
          <div className="stat-label">Total Services</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-success">{stats.operationalServices}</div>
          <div className="stat-label">Operational</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-warning">{stats.activeIncidents}</div>
          <div className="stat-label">Active Incidents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value text-info">{stats.scheduledMaintenance}</div>
          <div className="stat-label">Scheduled Maintenance</div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Services Status</h2>
          </div>
          {services.length > 0 ? (
            <div className="services-list">
              {services.map(service => (
                <div key={service.id} className="service-item">
                  <div className="service-info">
                    <h4>{service.name}</h4>
                    {service.description && (
                      <p className="text-muted text-small">{service.description}</p>
                    )}
                  </div>
                  <span className={`status-badge ${getStatusColor(service.status)}`}>
                    {service.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">No services configured yet.</p>
          )}
        </div>

        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Incidents</h2>
          </div>
          {incidents.length > 0 ? (
            <div className="incidents-list">
              {incidents.slice(0, 5).map(incident => (
                <div key={incident.id} className="incident-item">
                  <div className="incident-info">
                    <h4>{incident.title}</h4>
                    <div className="incident-meta">
                      <span className={`status-badge ${getIncidentStatusColor(incident.status)}`}>
                        {incident.status}
                      </span>
                      <span className="text-muted text-small">
                        {format(new Date(incident.created_at), 'MMM d, yyyy h:mm a')}
                      </span>
                      {incident.affected_services.length > 0 && (
                        <span className="text-muted text-small">
                          • Affects: {incident.affected_services.map(s => s.name).join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">No incidents reported.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
