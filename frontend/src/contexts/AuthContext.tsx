import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../api/client';
import wsClient from '../api/websocket';
import { User, Organization } from '../types';

interface AuthContextType {
  user: User | null;
  organizations: Organization[];
  currentOrg: Organization | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  setCurrentOrg: (org: Organization | null) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Connect WebSocket when user is authenticated
    const token = localStorage.getItem('access_token');
    if (user && token) {
      wsClient.connect(token);
    } else {
      wsClient.disconnect();
    }

    return () => {
      wsClient.disconnect();
    };
  }, [user]);

  useEffect(() => {
    // Join organization room when current org changes
    if (currentOrg) {
      wsClient.joinOrganization(currentOrg.id);
      
      return () => {
        wsClient.leaveOrganization(currentOrg.id);
      };
    }
  }, [currentOrg]);

  const loadUser = async () => {
    try {
      const response = await apiClient.getCurrentUser();
      setUser(response.user);
      setOrganizations(response.organizations);
      
      // Set first organization as current if available
      if (response.organizations.length > 0) {
        const savedOrgId = localStorage.getItem('current_org_id');
        const savedOrg = response.organizations.find((org: Organization) => org.id === savedOrgId);
        setCurrentOrg(savedOrg || response.organizations[0]);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password);
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    setUser(response.user);
    setOrganizations(response.organizations);
    
    if (response.organizations.length > 0) {
      setCurrentOrg(response.organizations[0]);
    }
  };

  const register = async (data: any) => {
    const response = await apiClient.register(data);
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    setUser(response.user);
    setOrganizations([response.organization]);
    setCurrentOrg(response.organization);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_org_id');
    wsClient.disconnect();
    setUser(null);
    setOrganizations([]);
    setCurrentOrg(null);
  };

  const handleSetCurrentOrg = (org: Organization | null) => {
    setCurrentOrg(org);
    if (org) {
      localStorage.setItem('current_org_id', org.id);
    } else {
      localStorage.removeItem('current_org_id');
    }
  };

  const refreshUser = async () => {
    await loadUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        currentOrg,
        isLoading,
        login,
        register,
        logout,
        setCurrentOrg: handleSetCurrentOrg,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
