import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { Team, User } from '../types';
import './Teams.css';

const Teams: React.FC = () => {
  const { currentOrg } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [selectedUserId, setSelectedUserId] = useState('');
  const [memberRole, setMemberRole] = useState('member');

  useEffect(() => {
    if (currentOrg) {
      loadTeams();
      loadUsers();
    }
  }, [currentOrg]);

  const loadTeams = async () => {
    if (!currentOrg) return;
    setIsLoading(true);
    try {
      const data = await apiClient.getTeams(currentOrg.id);
      setTeams(data.teams || []);
    } catch (error) {
      console.error('Failed to load teams:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUsers = async () => {
    if (!currentOrg) return;
    try {
      const data = await apiClient.getOrganizationUsers(currentOrg.id);
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    
    try {
      await apiClient.createTeam({
        ...formData,
        organization_id: currentOrg.id
      });
      
      setShowCreateModal(false);
      setFormData({ name: '', description: '' });
      loadTeams();
    } catch (error) {
      console.error('Failed to create team:', error);
      alert('Failed to create team');
    }
  };

  const handleUpdateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTeam) return;
    
    try {
      await apiClient.updateTeam(selectedTeam.id, formData);
      setShowEditModal(false);
      setSelectedTeam(null);
      setFormData({ name: '', description: '' });
      loadTeams();
    } catch (error) {
      console.error('Failed to update team:', error);
      alert('Failed to update team');
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    if (!window.confirm('Are you sure you want to delete this team?')) {
      return;
    }
    
    try {
      await apiClient.deleteTeam(teamId);
      loadTeams();
    } catch (error) {
      console.error('Failed to delete team:', error);
      alert('Failed to delete team');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTeam || !selectedUserId) return;
    
    try {
      await apiClient.addTeamMember(selectedTeam.id, {
        user_id: selectedUserId,
        role: memberRole
      });
      
      setSelectedUserId('');
      setMemberRole('member');
      loadTeamMembers(selectedTeam.id);
    } catch (error) {
      console.error('Failed to add team member:', error);
      alert('Failed to add team member');
    }
  };

  const handleRemoveMember = async (teamId: string, userId: string) => {
    if (!window.confirm('Are you sure you want to remove this member?')) {
      return;
    }
    
    try {
      await apiClient.removeTeamMember(teamId, userId);
      loadTeamMembers(teamId);
    } catch (error) {
      console.error('Failed to remove team member:', error);
      alert('Failed to remove team member');
    }
  };

  const loadTeamMembers = async (teamId: string) => {
    try {
      const data = await apiClient.getTeamMembers(teamId);
      const team = teams.find(t => t.id === teamId);
      if (team) {
        setSelectedTeam({ ...team, members: data.members || [] });
      }
    } catch (error) {
      console.error('Failed to load team members:', error);
    }
  };

  const openEditModal = (team: Team) => {
    setSelectedTeam(team);
    setFormData({
      name: team.name,
      description: team.description || ''
    });
    setShowEditModal(true);
  };

  const openMembersModal = async (team: Team) => {
    setSelectedTeam(team);
    await loadTeamMembers(team.id);
    setShowMembersModal(true);
  };

  if (isLoading) {
    return <div className="teams-loading">Loading teams...</div>;
  }

  return (
    <div className="teams-container">
      <div className="teams-header">
        <h1>Teams</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Create Team
        </button>
      </div>

      <div className="teams-grid">
        {teams.map((team) => (
          <div key={team.id} className="team-card">
            <div className="team-card-header">
              <h3>{team.name}</h3>
              <div className="team-actions">
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => openMembersModal(team)}
                  title="Manage Members"
                >
                  👥
                </button>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => openEditModal(team)}
                  title="Edit Team"
                >
                  ✏️
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDeleteTeam(team.id)}
                  title="Delete Team"
                >
                  🗑️
                </button>
              </div>
            </div>
            <p className="team-description">{team.description || 'No description'}</p>
            <div className="team-meta">
              <span>Members: {team.member_count || 0}</span>
              <span>Created: {new Date(team.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {teams.length === 0 && (
        <div className="teams-empty">
          <p>No teams yet. Create your first team to get started!</p>
        </div>
      )}

      {/* Create Team Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Team</h2>
              <button 
                className="modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleCreateTeam}>
              <div className="form-group">
                <label htmlFor="name">Team Name</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Team Modal */}
      {showEditModal && selectedTeam && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Team</h2>
              <button 
                className="modal-close"
                onClick={() => setShowEditModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleUpdateTeam}>
              <div className="form-group">
                <label htmlFor="edit-name">Team Name</label>
                <input
                  type="text"
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="edit-description">Description</label>
                <textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Team Members Modal */}
      {showMembersModal && selectedTeam && (
        <div className="modal-overlay" onClick={() => setShowMembersModal(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedTeam.name} - Members</h2>
              <button 
                className="modal-close"
                onClick={() => setShowMembersModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="team-members-section">
              <h3>Add Member</h3>
              <form onSubmit={handleAddMember} className="add-member-form">
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  required
                >
                  <option value="">Select a user...</option>
                  {users
                    .filter(u => !selectedTeam.members?.some(m => m.user_id === u.id))
                    .map(u => (
                      <option key={u.id} value={u.id}>
                        {u.first_name} {u.last_name} ({u.email})
                      </option>
                    ))}
                </select>
                <select
                  value={memberRole}
                  onChange={(e) => setMemberRole(e.target.value)}
                >
                  <option value="member">Member</option>
                  <option value="lead">Team Lead</option>
                </select>
                <button type="submit" className="btn btn-primary">
                  Add Member
                </button>
              </form>

              <h3>Current Members</h3>
              <div className="members-list">
                {selectedTeam.members?.map((member) => (
                  <div key={member.id} className="member-item">
                    <div className="member-info">
                      <strong>{member.user_name || member.user_email}</strong>
                      <span className="member-role">{member.role}</span>
                    </div>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleRemoveMember(selectedTeam.id, member.user_id)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                {(!selectedTeam.members || selectedTeam.members.length === 0) && (
                  <p className="no-members">No members in this team yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Teams;