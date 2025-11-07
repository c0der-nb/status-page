export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  is_superadmin: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string;
  role?: string;
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  organization_id: string;
  members_count?: number;
  services_count?: number;
  created_at: string;
}

export interface TeamMember {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  joined_at?: string;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  status: 'operational' | 'degraded' | 'partial_outage' | 'major_outage' | 'maintenance';
  organization_id: string;
  team_id?: string;
  team_name?: string;
  display_order: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceStatusHistory {
  id: string;
  status: string;
  reason: string;
  changed_by: string;
  created_at: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved' | 'scheduled' | 'in_progress' | 'completed';
  impact: 'none' | 'minor' | 'major' | 'critical';
  type: 'incident' | 'maintenance';
  scheduled_start?: string;
  scheduled_end?: string;
  resolved_at?: string;
  organization_id: string;
  created_by?: string;
  affected_services: Array<{ id: string; name: string }>;
  updates?: IncidentUpdate[];
  updates_count?: number;
  created_at: string;
  updated_at: string;
}

export interface IncidentUpdate {
  id: string;
  incident_id: string;
  status: string;
  message: string;
  user?: string;
  created_at: string;
}

export interface PublicStatusData {
  organization: {
    name: string;
    description: string;
  };
  overall_status: string;
  services: Array<{
    id: string;
    name: string;
    description: string;
    status: string;
  }>;
  active_incidents: Array<{
    id: string;
    title: string;
    status: string;
    impact: string;
    type: string;
    created_at: string;
    resolved_at?: string;
    latest_update?: {
      message: string;
      created_at: string;
    };
    affected_services: string[];
  }>;
  scheduled_maintenance: Array<{
    id: string;
    title: string;
    description: string;
    status: string;
    scheduled_start?: string;
    scheduled_end?: string;
    affected_services: string[];
  }>;
  incident_history: Array<{
    id: string;
    title: string;
    type: string;
    impact: string;
    status: string;
    created_at: string;
    resolved_at?: string;
    duration?: string;
  }>;
  last_updated: string;
}
