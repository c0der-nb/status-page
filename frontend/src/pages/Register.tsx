import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const Register: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    organizationName: '',
    organizationSlug: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Auto-generate slug from organization name
    if (name === 'organizationName') {
      const slug = value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      setFormData(prev => ({
        ...prev,
        organizationSlug: slug,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    setIsLoading(true);

    try {
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        organization_name: formData.organizationName,
        organization_slug: formData.organizationSlug,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to register. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: '500px' }}>
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Start monitoring your services today</p>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2">
            <div className="form-group">
              <label className="form-label">First Name</label>
              <input
                type="text"
                className="form-input"
                name="firstName"
                value={formData.firstName}
                onChange={handleChange}
                placeholder="John"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Last Name</label>
              <input
                type="text"
                className="form-input"
                name="lastName"
                value={formData.lastName}
                onChange={handleChange}
                placeholder="Doe"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email *</label>
            <input
              type="email"
              className="form-input"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Username *</label>
            <input
              type="text"
              className="form-input"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="johndoe"
              required
            />
          </div>

          <div className="grid grid-cols-2">
            <div className="form-group">
              <label className="form-label">Password *</label>
              <input
                type="password"
                className="form-input"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Min 6 characters"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password *</label>
              <input
                type="password"
                className="form-input"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm password"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Organization Name *</label>
            <input
              type="text"
              className="form-input"
              name="organizationName"
              value={formData.organizationName}
              onChange={handleChange}
              placeholder="My Company"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Organization URL Slug *</label>
            <input
              type="text"
              className="form-input"
              name="organizationSlug"
              value={formData.organizationSlug}
              onChange={handleChange}
              placeholder="my-company"
              required
            />
            <p className="form-hint">
              This will be used in your public status page URL: /status/{formData.organizationSlug || 'your-slug'}
            </p>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
