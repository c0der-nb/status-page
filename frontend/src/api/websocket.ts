import { io, Socket } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5010';

class WebSocketClient {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();

  connect(token: string) {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
    this.setupEventListeners();
  }

  connectPublic() {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(WS_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.emit('connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected');
    });

    // Service events
    this.socket.on('service_created', (data) => {
      this.emit('service_created', data);
    });

    this.socket.on('service_status_changed', (data) => {
      this.emit('service_status_changed', data);
    });

    this.socket.on('service_deleted', (data) => {
      this.emit('service_deleted', data);
    });

    // Incident events
    this.socket.on('incident_created', (data) => {
      this.emit('incident_created', data);
    });

    this.socket.on('incident_updated', (data) => {
      this.emit('incident_updated', data);
    });

    this.socket.on('incident_update_added', (data) => {
      this.emit('incident_update_added', data);
    });

    this.socket.on('incident_deleted', (data) => {
      this.emit('incident_deleted', data);
    });

    // Public events (for public status page)
    this.socket.on('public_service_created', (data) => {
      this.emit('public_service_created', data);
    });

    this.socket.on('public_service_status_changed', (data) => {
      this.emit('public_service_status_changed', data);
    });

    this.socket.on('public_incident_created', (data) => {
      this.emit('public_incident_created', data);
    });

    this.socket.on('public_incident_updated', (data) => {
      this.emit('public_incident_updated', data);
    });

    this.socket.on('public_incident_update_added', (data) => {
      this.emit('public_incident_update_added', data);
    });

    // Error handling
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinOrganization(organizationId: string) {
    if (this.socket?.connected) {
      this.socket.emit('join_organization', { organization_id: organizationId });
    }
  }

  leaveOrganization(organizationId: string) {
    if (this.socket?.connected) {
      this.socket.emit('leave_organization', { organization_id: organizationId });
    }
  }

  joinPublicStatus(orgSlug: string) {
    if (this.socket?.connected) {
      this.socket.emit('join_public_status', { org_slug: orgSlug });
    }
  }

  leavePublicStatus(orgSlug: string) {
    if (this.socket?.connected) {
      this.socket.emit('leave_public_status', { org_slug: orgSlug });
    }
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export default new WebSocketClient();
