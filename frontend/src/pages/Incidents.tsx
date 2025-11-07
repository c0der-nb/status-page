import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { Incident, Service } from '../types';
import { format } from 'date-fns';

const Incidents: React.FC = () => {
  const { currentOrg } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'incident',
    status: 'investigating',
    impact: 'none',
    service_ids: [] as string[],
    initial_message: '',
  });

  useEffect(() => {
    if (currentOrg) {
      loadData();
    }
  }, [currentOrg]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [incidentsRes, servicesRes] = await Promise.all([
        apiClient.getIncidents(currentOrg!.id),
        apiClient.getServices(currentOrg!.id),
      ]);
      setIncidents(incidentsRes.incidents);
      setServices(servicesRes.services);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createIncident({
        ...formData,
        organization_id: currentOrg!.id,
      });
      setShowCreateModal(false);
      setFormData({
        title: '',
        description: '',
        type: 'incident',
        status: 'investigating',
        impact: 'none',
        service_ids: [],
        initial_message: '',
      });
      loadData();
    } catch (error) {
      console.error('Failed to create incident:', error);
      alert('Failed to create incident');
    }
  };

  const handleAddUpdate = async (incidentId: string, message: string) => {
    try {
      await apiClient.addIncidentUpdate(incidentId, message);
      loadData();
    } catch (error) {
      console.error('Failed to add update:', error);
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
    <div>
      <div className="page-header">
        <div>
          <h1>Incidents & Maintenance</h1>
          <p className="text-muted">Manage incidents and scheduled maintenance</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          Report Incident
        </button>
      </div>

      {incidents.length === 0 ? (
        <div className="card text-center">
          <h3>No incidents reported</h3>
          <p className="text-muted">All systems are operational</p>
        </div>
      ) : (
        <div>
          {incidents.map(incident => (
            <div key={incident.id} className="card">
              <div className="card-header">
                <div>
                  <h3>{incident.title}</h3>
                  <div className="flex gap-2 mt-2">
                    <span className={`status-badge status-${incident.status === 'resolved' ? 'operational' : 'major-outage'}`}>
                      {incident.status}
                    </span>
                    <span className={`status-badge status-${incident.impact}`}>
                      {incident.impact} impact
                    </span>
                    <span className="text-small text-muted">
                      {format(new Date(incident.created_at), 'MMM d, yyyy h:mm a')}
                    </span>
                  </div>
                </div>
              </div>
              
              {incident.description && (
                <p className="text-muted">{incident.description}</p>
              )}
              
              {incident.affected_services.length > 0 && (
                <div className="mb-3">
                  <strong>Affected Services:</strong>{' '}
                  {incident.affected_services.map(s => s.name).join(', ')}
                </div>
              )}

              {incident.status !== 'resolved' && (
                <div className="mt-3">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const input = e.currentTarget.elements.namedItem('update') as HTMLInputElement;
                      if (input.value) {
                        handleAddUpdate(incident.id, input.value);
                        input.value = '';
                      }
                    }}
                    className="flex gap-2"
                  >
                    <input
                      name="update"
                      type="text"
                      className="form-input"
                      placeholder="Add an update..."
                    />
                    <button type="submit" className="btn btn-primary">
                      Add Update
                    </button>
                  </form>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Report New Incident</h2>
            </div>
            
            <form onSubmit={handleCreateIncident}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Title *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-textarea"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                  />
                </div>

                <div className="grid grid-cols-2">
                  <div className="form-group">
                    <label className="form-label">Type</label>
                    <select
                      className="form-select"
                      value={formData.type}
                      onChange={(e) => setFormData({...formData, type: e.target.value})}
                    >
                      <option value="incident">Incident</option>
                      <option value="maintenance">Maintenance</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Impact</label>
                    <select
                      className="form-select"
                      value={formData.impact}
                      onChange={(e) => setFormData({...formData, impact: e.target.value})}
                    >
                      <option value="none">None</option>
                      <option value="minor">Minor</option>
                      <option value="major">Major</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Affected Services</label>
                  <select
                    multiple
                    className="form-select"
                    style={{ height: '100px' }}
                    value={formData.service_ids}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setFormData({...formData, service_ids: selected});
                    }}
                  >
                    {services.map(service => (
                      <option key={service.id} value={service.id}>
                        {service.name}
                      </option>
                    ))}
                  </select>
                  <p className="form-hint">Hold Ctrl/Cmd to select multiple</p>
                </div>

                <div className="form-group">
                  <label className="form-label">Initial Message</label>
                  <textarea
                    className="form-textarea"
                    value={formData.initial_message}
                    onChange={(e) => setFormData({...formData, initial_message: e.target.value})}
                    placeholder="We are investigating..."
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Incidents;
