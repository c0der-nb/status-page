import React, { useState, useEffect } from 'react';
import { Service, Team } from '../types';

interface ServiceModalProps {
  service: Service | null;
  teams: Team[];
  onClose: () => void;
  onSave: (data: any) => void;
}

const ServiceModal: React.FC<ServiceModalProps> = ({ service, teams, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    team_id: '',
    status: 'operational',
    is_public: true,
  });

  useEffect(() => {
    if (service) {
      setFormData({
        name: service.name,
        description: service.description,
        team_id: service.team_id || '',
        status: service.status,
        is_public: service.is_public,
      });
    }
  }, [service]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{service ? 'Edit Service' : 'Add Service'}</h2>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Service Name *</label>
              <input
                type="text"
                className="form-input"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                className="form-textarea"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Assigned Team</label>
              <select
                className="form-select"
                name="team_id"
                value={formData.team_id}
                onChange={handleChange}
              >
                <option value="">No team assigned</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Initial Status</label>
              <select
                className="form-select"
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="operational">Operational</option>
                <option value="degraded">Degraded Performance</option>
                <option value="partial_outage">Partial Outage</option>
                <option value="major_outage">Major Outage</option>
                <option value="maintenance">Under Maintenance</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-checkbox">
                <input
                  type="checkbox"
                  name="is_public"
                  checked={formData.is_public}
                  onChange={handleChange}
                />
                Show on public status page
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {service ? 'Update' : 'Create'} Service
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ServiceModal;
