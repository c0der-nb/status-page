import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Organization: React.FC = () => {
  const { currentOrg } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1>Organization Settings</h1>
        <p className="text-muted">Manage your organization settings and members</p>
      </div>
      
      <div className="card">
        <h3>Organization Details</h3>
        <div className="form-group">
          <label className="form-label">Name</label>
          <p>{currentOrg?.name}</p>
        </div>
        <div className="form-group">
          <label className="form-label">Slug</label>
          <p>{currentOrg?.slug}</p>
        </div>
        <div className="form-group">
          <label className="form-label">Public Status Page URL</label>
          <p>
            <a href={`/status/${currentOrg?.slug}`} target="_blank" rel="noopener noreferrer">
              {window.location.origin}/status/{currentOrg?.slug}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Organization;
