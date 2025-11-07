import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../api/client';
import wsClient from '../api/websocket';
import { PublicStatusData } from '../types';
import { format } from 'date-fns';
import './PublicStatus.css';

const PublicStatus: React.FC = () => {
  const { orgSlug } = useParams<{ orgSlug: string }>();
  const [statusData, setStatusData] = useState<PublicStatusData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [subscribeMessage, setSubscribeMessage] = useState('');

  useEffect(() => {
    if (orgSlug) {
      loadStatusData();
      
      // Connect to WebSocket without authentication for public page
      wsClient.connectPublic();
      
      // Wait a bit for connection to establish, then join public room
      setTimeout(() => {
        wsClient.joinPublicStatus(orgSlug);
      }, 500);
      
      // Set up real-time event listeners
      const handleServiceStatusChanged = (data: any) => {
        console.log('Service status changed:', data);
        setStatusData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            services: prev.services.map((service) =>
              service.id === data.service.id
                ? { ...service, status: data.service.status }
                : service
            ),
          };
        });
      };

      const handleServiceCreated = (data: any) => {
        console.log('Service created:', data);
        setStatusData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            services: [...prev.services, data.service].sort((a, b) => a.display_order - b.display_order),
          };
        });
      };

      const handleIncidentCreated = (data: any) => {
        console.log('Incident created:', data);
        setStatusData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            active_incidents: [data.incident, ...prev.active_incidents],
          };
        });
      };

      const handleIncidentUpdated = (data: any) => {
        console.log('Incident updated:', data);
        setStatusData((prev) => {
          if (!prev) return prev;
          const isResolved = data.incident.status === 'resolved' || data.incident.status === 'completed';
          
          if (isResolved) {
            // Move from active to history
            return {
              ...prev,
              active_incidents: prev.active_incidents.filter((inc: any) => inc.id !== data.incident.id),
              incident_history: [data.incident, ...prev.incident_history].slice(0, 10),
            };
          } else {
            // Update in active incidents
            return {
              ...prev,
              active_incidents: prev.active_incidents.map((inc: any) =>
                inc.id === data.incident.id ? { ...inc, ...data.incident } : inc
              ),
            };
          }
        });
      };

      const handleIncidentUpdateAdded = (data: any) => {
        console.log('Incident update added:', data);
        setStatusData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            active_incidents: prev.active_incidents.map((inc: any) =>
              inc.id === data.incident_id
                ? {
                    ...inc,
                    updates: inc.updates ? [data.update, ...inc.updates] : [data.update],
                  }
                : inc
            ),
          };
        });
      };

      // Subscribe to events
      wsClient.on('public_service_status_changed', handleServiceStatusChanged);
      wsClient.on('public_service_created', handleServiceCreated);
      wsClient.on('public_incident_created', handleIncidentCreated);
      wsClient.on('public_incident_updated', handleIncidentUpdated);
      wsClient.on('public_incident_update_added', handleIncidentUpdateAdded);
      
      return () => {
        // Unsubscribe from events
        wsClient.off('public_service_status_changed', handleServiceStatusChanged);
        wsClient.off('public_service_created', handleServiceCreated);
        wsClient.off('public_incident_created', handleIncidentCreated);
        wsClient.off('public_incident_updated', handleIncidentUpdated);
        wsClient.off('public_incident_update_added', handleIncidentUpdateAdded);
        wsClient.leavePublicStatus(orgSlug);
      };
    }
  }, [orgSlug]);

  const loadStatusData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.getPublicStatus(orgSlug!);
      setStatusData(data);
    } catch (err: any) {
      setError('Failed to load status page. Please try again later.');
      console.error('Failed to load status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await apiClient.subscribeToUpdates(orgSlug!, email);
      setSubscribeMessage('Successfully subscribed to status updates!');
      setEmail('');
      setTimeout(() => setSubscribeMessage(''), 5000);
    } catch (err) {
      setSubscribeMessage('Failed to subscribe. Please try again.');
      setTimeout(() => setSubscribeMessage(''), 5000);
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'overall-operational';
      case 'degraded': return 'overall-degraded';
      case 'partial_outage': return 'overall-partial';
      case 'major_outage': return 'overall-major';
      case 'maintenance': return 'overall-maintenance';
      default: return '';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return '✓';
      case 'degraded': return '!';
      case 'partial_outage': return '⚠';
      case 'major_outage': return '✕';
      case 'maintenance': return '🔧';
      default: return '?';
    }
  };

  if (isLoading) {
    return (
      <div className="public-status-page">
        <div className="loading-container">
          <div className="spinner spinner-lg"></div>
        </div>
      </div>
    );
  }

  if (error || !statusData) {
    return (
      <div className="public-status-page">
        <div className="error-container">
          <h2>Unable to Load Status Page</h2>
          <p>{error || 'Status page not found'}</p>
        </div>
      </div>
    );
  }

  const overallStatusText = statusData.overall_status === 'operational' 
    ? 'All Systems Operational'
    : statusData.overall_status === 'maintenance'
    ? 'Scheduled Maintenance'
    : 'System Issues Detected';

  return (
    <div className="public-status-page">
      <header className="status-header">
        <div className="status-container">
          <h1>{statusData.organization.name} Status</h1>
          {statusData.organization.description && (
            <p className="org-description">{statusData.organization.description}</p>
          )}
        </div>
      </header>

      <div className={`overall-status ${getOverallStatusColor(statusData.overall_status)}`}>
        <div className="status-container">
          <div className="overall-status-content">
            <span className="status-icon">{getStatusIcon(statusData.overall_status)}</span>
            <h2>{overallStatusText}</h2>
          </div>
        </div>
      </div>

      <div className="status-container">
        {/* Active Incidents */}
        {statusData.active_incidents.length > 0 && (
          <section className="status-section">
            <h3>Active Incidents</h3>
            {statusData.active_incidents.map(incident => (
              <div key={incident.id} className="incident-card">
                <div className="incident-header">
                  <h4>{incident.title}</h4>
                  <span className={`status-badge status-${incident.impact}`}>
                    {incident.impact} impact
                  </span>
                </div>
                {incident.latest_update && (
                  <div className="incident-update">
                    <p>{incident.latest_update.message}</p>
                    <span className="update-time">
                      {format(new Date(incident.latest_update.created_at), 'MMM d, h:mm a')}
                    </span>
                  </div>
                )}
                {incident.affected_services.length > 0 && (
                  <div className="affected-services">
                    Affected services: {incident.affected_services.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </section>
        )}

        {/* Scheduled Maintenance */}
        {statusData.scheduled_maintenance.length > 0 && (
          <section className="status-section">
            <h3>Scheduled Maintenance</h3>
            {statusData.scheduled_maintenance.map(maintenance => (
              <div key={maintenance.id} className="maintenance-card">
                <h4>{maintenance.title}</h4>
                {maintenance.description && <p>{maintenance.description}</p>}
                <div className="maintenance-schedule">
                  {maintenance.scheduled_start && (
                    <span>
                      Starts: {format(new Date(maintenance.scheduled_start), 'MMM d, h:mm a')}
                    </span>
                  )}
                  {maintenance.scheduled_end && (
                    <span>
                      Ends: {format(new Date(maintenance.scheduled_end), 'MMM d, h:mm a')}
                    </span>
                  )}
                </div>
                {maintenance.affected_services.length > 0 && (
                  <div className="affected-services">
                    Affected services: {maintenance.affected_services.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </section>
        )}

        {/* Services Status */}
        <section className="status-section">
          <h3>Services</h3>
          <div className="services-status-list">
            {statusData.services.map(service => (
              <div key={service.id} className="service-status-item">
                <div className="service-name">
                  {service.name}
                  {service.description && (
                    <span className="service-desc">{service.description}</span>
                  )}
                </div>
                <div className={`service-status status-${service.status}`}>
                  <span className="status-icon">{getStatusIcon(service.status)}</span>
                  <span className="status-text">{service.status.replace('_', ' ')}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Incident History */}
        {statusData.incident_history.length > 0 && (
          <section className="status-section">
            <h3>Incident History (Last 7 Days)</h3>
            <div className="history-list">
              {statusData.incident_history.map(incident => (
                <div key={incident.id} className="history-item">
                  <div className="history-date">
                    {format(new Date(incident.created_at), 'MMM d')}
                  </div>
                  <div className="history-content">
                    <h5>{incident.title}</h5>
                    <div className="history-meta">
                      <span className={`status-badge status-${incident.impact}`}>
                        {incident.impact}
                      </span>
                      <span className="history-status">{incident.status}</span>
                      {incident.duration && (
                        <span className="history-duration">Duration: {incident.duration}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Subscribe Section */}
        <section className="subscribe-section">
          <h3>Subscribe to Updates</h3>
          <p>Get notified about incidents and maintenance via email</p>
          <form onSubmit={handleSubscribe} className="subscribe-form">
            <input
              type="email"
              className="form-input"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-primary">
              Subscribe
            </button>
          </form>
          {subscribeMessage && (
            <p className="subscribe-message">{subscribeMessage}</p>
          )}
        </section>

        <footer className="status-footer">
          <p>Last updated: {format(new Date(statusData.last_updated), 'MMM d, yyyy h:mm a')}</p>
        </footer>
      </div>
    </div>
  );
};

export default PublicStatus;
