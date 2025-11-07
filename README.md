# Status Page Application

A comprehensive status page application similar to StatusPage.io, built with React (TypeScript) for the frontend, Flask (Python) for the backend, and PostgreSQL for the database.

## Features

### Core Functionality
- **Multi-tenant Architecture**: Support for multiple organizations with isolated data
- **User Authentication & Authorization**: JWT-based authentication with role-based access control
- **Team Management**: Organize users into teams within organizations
- **Service Management**: CRUD operations for services with status tracking
- **Incident Management**: Create, update, and resolve incidents with timeline tracking
- **Maintenance Scheduling**: Plan and communicate scheduled maintenance
- **Real-time Updates**: WebSocket-based real-time status updates
- **Public Status Page**: Beautiful, responsive public-facing status page for each organization

### Service Status Options
- Operational
- Degraded Performance
- Partial Outage
- Major Outage
- Under Maintenance

### Incident Management Features
- Multiple incident types (Incident, Maintenance)
- Impact levels (None, Minor, Major, Critical)
- Status tracking (Investigating, Identified, Monitoring, Resolved)
- Timeline updates with user attribution
- Service associations

## Tech Stack

### Backend
- **Flask**: Python web framework
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-JWT-Extended**: JWT authentication
- **Flask-SocketIO**: WebSocket support for real-time updates
- **PostgreSQL**: Primary database
- **Flask-Migrate**: Database migrations
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **React 18**: UI framework with TypeScript
- **React Router v6**: Client-side routing
- **Socket.io Client**: Real-time WebSocket connections
- **Axios**: HTTP client for API calls
- **date-fns**: Date formatting utilities
- **Pure CSS**: Custom styling without external frameworks

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- npm or yarn

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/c0der-nb/status-page
```

### 2. Database Setup

Create a PostgreSQL database in a docker container:
```bash
docker run --name my-postgres \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -d postgres:15

```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp env.example .env

# Edit .env file with your configuration
# Update DATABASE_URL with your PostgreSQL credentials:
# DATABASE_URL=postgresql://username:password@localhost:5432/statuspage_db

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the backend server
python app.py
```

The backend will run on `http://localhost:5006`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:5006/api" > .env
echo "REACT_APP_WS_URL=http://localhost:5006" >> .env

# Start development server
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

### 1. Register a New Account
- Navigate to `http://localhost:3000/register`
- Fill in your details and organization information
- The organization slug will be used for your public status page URL

### 2. Login
- Navigate to `http://localhost:3000/login`
- Use your email and password to login

### 3. Dashboard
After logging in, you'll see:
- Overview of all services and their current status
- Active incidents and their impact
- Recent incident history
- Quick stats about your status page

### 4. Managing Services
- Navigate to the Services page
- Click "Add Service" to create a new service
- Set the service name, description, team assignment, and initial status
- Services can be marked as public (shown on status page) or private

### 5. Managing Incidents
- Navigate to the Incidents page
- Click "Report Incident" to create a new incident
- Select affected services and set impact level
- Add updates to keep users informed
- Resolve incidents when issues are fixed

### 6. Public Status Page
- Your public status page is available at: `http://localhost:3000/status/[your-org-slug]`
- Shows current status of all public services
- Displays active incidents and scheduled maintenance
- Includes incident history for the last 7 days
- Users can subscribe for email notifications (placeholder functionality)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user and organization
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Organizations
- `GET /api/organizations` - List user's organizations
- `POST /api/organizations` - Create new organization
- `GET /api/organizations/:id` - Get organization details
- `PUT /api/organizations/:id` - Update organization
- `DELETE /api/organizations/:id` - Delete organization
- `GET /api/organizations/:id/members` - List organization members
- `POST /api/organizations/:id/members` - Add member
- `PUT /api/organizations/:id/members/:userId` - Update member role
- `DELETE /api/organizations/:id/members/:userId` - Remove member

### Services
- `GET /api/services?org_id=:orgId` - List services
- `POST /api/services` - Create service
- `GET /api/services/:id` - Get service details
- `PUT /api/services/:id` - Update service
- `DELETE /api/services/:id` - Delete service
- `POST /api/services/reorder` - Reorder services

### Incidents
- `GET /api/incidents?org_id=:orgId` - List incidents
- `POST /api/incidents` - Create incident
- `GET /api/incidents/:id` - Get incident details
- `PUT /api/incidents/:id` - Update incident
- `DELETE /api/incidents/:id` - Delete incident
- `POST /api/incidents/:id/updates` - Add incident update

### Teams
- `GET /api/teams?org_id=:orgId` - List teams
- `POST /api/teams` - Create team
- `GET /api/teams/:id` - Get team details
- `PUT /api/teams/:id` - Update team
- `DELETE /api/teams/:id` - Delete team
- `POST /api/teams/:id/members` - Add team member
- `DELETE /api/teams/:id/members/:userId` - Remove team member

### Public Status
- `GET /api/public/status/:orgSlug` - Get public status page data
- `GET /api/public/status/:orgSlug/incidents/:id` - Get public incident details
- `POST /api/public/status/:orgSlug/subscribe` - Subscribe to updates

## WebSocket Events

### Client Events
- `connect` - Establish connection with JWT token
- `join_organization` - Join organization room for updates
- `leave_organization` - Leave organization room
- `join_public_status` - Join public status page room
- `leave_public_status` - Leave public status page room

### Server Events
- `service_created` - New service created
- `service_status_changed` - Service status updated
- `service_deleted` - Service removed
- `incident_created` - New incident reported
- `incident_updated` - Incident status changed
- `incident_update_added` - New update added to incident
- `incident_deleted` - Incident removed

## Security Features

- JWT-based authentication with refresh tokens
- Password hashing using bcrypt
- Role-based access control (Admin, Member, Viewer)
- Organization-level data isolation
- CORS configuration for API security
- SQL injection prevention through ORM
- XSS protection in React

## Database Schema

### Main Tables
- **users**: User accounts with authentication
- **organizations**: Multi-tenant organizations
- **services**: Monitored services
- **incidents**: Incidents and maintenance records
- **incident_updates**: Timeline updates for incidents
- **teams**: Teams within organizations
- **team_members**: Team membership records
- **service_status_history**: Historical status changes

### Association Tables
- **user_organizations**: User-organization relationships with roles
- **incident_services**: Many-to-many incident-service relationships

## Development

### Running Tests
```bash
# Backend tests (to be implemented)
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

#### Backend
```bash
cd backend
# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False
# Run with production WSGI server like Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Frontend
```bash
cd frontend
npm run build
# Serve the build folder with any static file server
```
