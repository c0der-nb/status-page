import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Layout.css';

const Layout: React.FC = () => {
  const { user, currentOrg, organizations, setCurrentOrg, logout } = useAuth();
  const navigate = useNavigate();
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleOrgChange = (org: any) => {
    setCurrentOrg(org);
    setShowOrgDropdown(false);
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="logo">StatusPage</h1>
            {currentOrg && (
              <div className="org-selector">
                <button
                  className="org-selector-btn"
                  onClick={() => setShowOrgDropdown(!showOrgDropdown)}
                >
                  {currentOrg.name}
                  <span className="dropdown-arrow">▼</span>
                </button>
                {showOrgDropdown && (
                  <div className="dropdown-menu">
                    {organizations.map((org) => (
                      <button
                        key={org.id}
                        className={`dropdown-item ${org.id === currentOrg.id ? 'active' : ''}`}
                        onClick={() => handleOrgChange(org)}
                      >
                        {org.name}
                        <span className="org-role">{org.role}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="header-right">
            {currentOrg && (
              <a
                href={`/status/${currentOrg.slug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline btn-sm"
              >
                View Public Page
              </a>
            )}
            <div className="user-menu">
              <button
                className="user-menu-btn"
                onClick={() => setShowUserDropdown(!showUserDropdown)}
              >
                {user?.username}
                <span className="dropdown-arrow">▼</span>
              </button>
              {showUserDropdown && (
                <div className="dropdown-menu dropdown-menu-right">
                  <div className="dropdown-header">
                    <div>{user?.first_name} {user?.last_name}</div>
                    <div className="text-small text-muted">{user?.email}</div>
                  </div>
                  <button className="dropdown-item" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="layout-body">
        <nav className="sidebar">
          <div className="nav-links">
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">📊</span>
              Dashboard
            </NavLink>
            <NavLink to="/services" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">🔧</span>
              Services
            </NavLink>
            <NavLink to="/incidents" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">⚠️</span>
              Incidents
            </NavLink>
            <NavLink to="/teams" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">👥</span>
              Teams
            </NavLink>
            <NavLink to="/organization" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">🏢</span>
              Organization
            </NavLink>
          </div>
        </nav>

        <main className="main-content">
          <div className="container">
            {currentOrg ? (
              <Outlet />
            ) : (
              <div className="no-org-message">
                <h2>No Organization Selected</h2>
                <p>Please select an organization to continue.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
