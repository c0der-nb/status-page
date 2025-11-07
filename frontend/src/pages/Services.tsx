import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { Service, Team } from '../types';
import ServiceModal from '../components/ServiceModal';
import './Services.css';

const Services: React.FC = () => {
  const { currentOrg } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);

  useEffect(() => {
    if (currentOrg) {
      loadData();
    }
  }, [currentOrg]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [servicesRes, teamsRes] = await Promise.all([
        apiClient.getServices(currentOrg!.id),
        apiClient.getTeams(currentOrg!.id),
      ]);
      setServices(servicesRes.services);
      setTeams(teamsRes.teams);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingService(null);
    setShowModal(true);
  };

  const handleEdit = (service: Service) => {
    setEditingService(service);
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this service?')) {
      return;
    }

    try {
      await apiClient.deleteService(id);
      setServices(services.filter(s => s.id !== id));
    } catch (error) {
      console.error('Failed to delete service:', error);
      alert('Failed to delete service');
    }
  };

  const handleStatusChange = async (service: Service, newStatus: string) => {
    try {
      await apiClient.updateService(service.id, { 
        status: newStatus,
        status_reason: `Status changed to ${newStatus}`,
      });
      setServices(services.map(s => 
        s.id === service.id ? { ...s, status: newStatus as any } : s
      ));
    } catch (error) {
      console.error('Failed to update status:', error);
      alert('Failed to update service status');
    }
  };

  const handleSave = async (data: any) => {
    try {
      if (editingService) {
        const updated = await apiClient.updateService(editingService.id, data);
        setServices(services.map(s => s.id === editingService.id ? updated : s));
      } else {
        const created = await apiClient.createService({
          ...data,
          organization_id: currentOrg!.id,
        });
        setServices([...services, created]);
      }
      setShowModal(false);
    } catch (error) {
      console.error('Failed to save service:', error);
      alert('Failed to save service');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'status-operational';
      case 'degraded': return 'status-degraded';
      case 'partial_outage': return 'status-partial-outage';
      case 'major_outage': return 'status-major-outage';
      case 'maintenance': return 'status-maintenance';
      default: return '';
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
    <div className="services-page">
      <div className="page-header">
        <div>
          <h1>Services</h1>
          <p className="text-muted">Manage your monitored services</p>
        </div>
        <button className="btn btn-primary" onClick={handleCreate}>
          Add Service
        </button>
      </div>

      {services.length === 0 ? (
        <div className="empty-state">
          <h3>No services yet</h3>
          <p className="text-muted">Add your first service to start monitoring</p>
          <button className="btn btn-primary" onClick={handleCreate}>
            Add Your First Service
          </button>
        </div>
      ) : (
        <div className="services-grid">
          {services.map(service => (
            <div key={service.id} className="service-card">
              <div className="service-card-header">
                <h3>{service.name}</h3>
                <div className="service-actions">
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => handleEdit(service)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(service.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <p className="service-description">{service.description || 'No description'}</p>
              
              <div className="service-meta">
                {service.team_name && (
                  <span className="meta-item">Team: {service.team_name}</span>
                )}
                <span className="meta-item">
                  {service.is_public ? 'Public' : 'Private'}
                </span>
              </div>

              <div className="service-status">
                <label className="text-small text-muted">Current Status:</label>
                <select
                  className="form-select"
                  value={service.status}
                  onChange={(e) => handleStatusChange(service, e.target.value)}
                >
                  <option value="operational">Operational</option>
                  <option value="degraded">Degraded Performance</option>
                  <option value="partial_outage">Partial Outage</option>
                  <option value="major_outage">Major Outage</option>
                  <option value="maintenance">Under Maintenance</option>
                </select>
              </div>

              <div className="service-card-footer">
                <span className={`status-badge ${getStatusColor(service.status)}`}>
                  {service.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <ServiceModal
          service={editingService}
          teams={teams}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default Services;
