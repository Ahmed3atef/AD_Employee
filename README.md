# ADIWA - Active Directory Integration Web Application

A Django-based web application that integrates with Microsoft Active Directory (AD) for user authentication and management, with MS SQL Server as the database backend.

## ✨ Features

### Core Features
- **Active Directory Authentication**: Authenticate users against your AD infrastructure
- **Employee Management**: Manage employee profiles with AD synchronization
- **Create AD Users**: Create new users directly in Active Directory from the admin panel
- **Change AD Passwords**: Reset user passwords in Active Directory without storing credentials locally
- **OU Transfer**: Transfer employees between Organizational Units with full audit logging
- **Idempotent User Sync**: Sync users from AD — only new or changed records are updated
- **Department Management**: Organize employees by departments mapped to AD OUs
- **Job Title Management**: Track employee job titles synced from AD
- **Comprehensive Audit Logging**: Track all OU transfer operations with detailed logs

### Technical Features
- RESTful API built with Django REST Framework
- JWT-based authentication
- MS SQL Server database integration
- LDAP3 for Active Directory operations
- Interactive API documentation (Swagger/ReDoc)
- Admin interface with Jazzmin theme
- Real-time AD user synchronization
- Cached credential storage for AD operations
- Docker-based development environment with health-check polling

## 🏗️ Architecture

```
┌─────────────────┐
│   HTML/CSS/JS   │
│   Frontend      │
└────────┬────────┘
         │
         │ REST API (JWT)
         │
┌────────▼────────┐
│  Django Backend │
│  - Auth         │
│  - Employee API │
│  - Admin Panel  │
└────┬─────┬──────┘
     │     │
     │     │ LDAP
     │     │
┌──────────▼──────┐
│ Active Directory│
│  (Samba Domain) │
└─────────────────┘
     │
     │ SQL
     │
┌────▼─────────────┐
│  MS SQL Server   │
│  (adiwa_db)      │
└──────────────────┘
```

## 📦 Prerequisites

### For Docker Deployment (Recommended)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### For Manual Installation
- Python 3.14+
- MS SQL Server 2022+
- Active Directory Server (or Samba AD DC)
- ODBC Driver 18 for SQL Server

## 🚀 Installation

### Using Docker Compose (Recommended)
- Requires an AD server

1- Make sure you have Docker and Docker Compose installed on your system
and create a `docker-compose.yml` file with this script:

```docker-compose
services:
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: mssql_server
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SaPass@ADIWA
      - MSSQL_PID=Developer
    ports:
      - "1433:1433"
    volumes:
      - mssql_data:/var/opt/mssql
    networks:
      - assessment_network
    healthcheck:
      test: /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P SaPass@ADIWA -Q "SELECT 1" -C || exit 1
      interval: 10s
      timeout: 3s
      retries: 10
      start_period: 10s
    command: >
      /bin/bash -c "
      /opt/mssql/bin/sqlservr &
      sleep 30 &&
      /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P SaPass@ADIWA -Q 'CREATE DATABASE adiwa_db' -C &&
      wait
      "

  django_app:
    image: ahmedatef101/ad-employee:latest
    container_name: django_app
    environment:
      - SECRET_KEY=django-insecure-ql^cl-(5mgbjtj3g#-7gyyoj3%3+(1(teu4r!lyt^9+9#bw&i@
      - DEBUG=True

      # MS SQL Server Configuration
      - DB_ENGINE=mssql
      - DB_NAME=adiwa_db
      - DB_USER=sa
      - DB_PASSWORD=SaPass@ADIWA
      - DB_HOST=mssql
      - DB_PORT=1433

      # Active Directory Configuration (adjust based on your setup)
      # If AD runs in separate Docker Compose (from SERVERS_DOCKER):
      - AD_SERVER=ldap://172.20.0.10:389
      # If AD runs on host machine:
      #- AD_SERVER=ldap://host.docker.internal:389
      
      - AD_DOMAIN=eissa.local
      - AD_BASE_DN=DC=eissa,DC=local
      - AD_CONTAINER_DN_BASE=OU=New,DC=eissa,DC=local
      
      # Frontend
      - BASE_URL=http://[IP_ADDRESS]/api/
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    networks:
      - assessment_network
    depends_on:
      mssql:
        condition: service_healthy
    command: >
      /bin/bash -c "
      sleep 10 &&
      python manage.py migrate &&
      python manage.py create_default_superuser &&
      python manage.py runserver 0.0.0.0:8000
      "

networks:
  assessment_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16

volumes:
  mssql_data:
```

2- Run this command:
```bash
docker-compose up -d
```


### Using Docker
- Requires an AD server

This setup uses Docker Compose to run the Active Directory (AD) server, MS SQL Server, and the Django application, creating a complete local development environment.

#### 1. Clone the Repository
```bash
git clone https://github.com/Ahmed3atef/AD_Employee.git
cd AD_Employee
```

#### 2. Set Up Environment Variables
```bash
cp .ex.env .env
# Edit .env with your configuration.
# Ensure 'AD_SERVER' is correctly set. If using the SERVERS_DOCKER setup (Step 3),
# this will typically be the IP address assigned to the AD server within the docker network,
# such as ldap://172.20.0.10:389, as configured in the main docker-compose.yml.
```

#### 3. Start Active Directory Server
Navigate to the `SERVERS_DOCKER` directory and run the `start.sh` script. This will bring up the AD server in a separate Docker Compose setup, making it accessible to your main application.
```bash
cd SERVERS_DOCKER
./start.sh
cd ..
```
*Wait for the AD server to be fully operational before proceeding. You can monitor its logs if needed.*

#### 4. Build and Start the Application
From the project root directory (`AD_Employee`), use Docker Compose to build the Django application image and start the application services (Django app and its dedicated MS SQL Server). Database migrations and the creation of a default superuser will be handled automatically upon application startup.
```bash
docker-compose up --build -d
```

The application will be available at:
- Frontend: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/schema/swagger-ui/

### Manual Installation

#### 1. Clone and Setup Python Environment
```bash
git clone https://github.com/Ahmed3atef/AD_Employee.git
cd ADIWA
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Database and AD
Edit `.env` file with your configuration:
```env
SECRET_KEY=your-secret-key
DEBUG=True

# MS SQL Server
DB_ENGINE=mssql
DB_NAME=adiwa_db
DB_USER=sa
DB_PASSWORD=YourPassword
DB_HOST=localhost
DB_PORT=1433

# Active Directory
AD_SERVER=ldap://your-ad-server:389
AD_DOMAIN=yourdomain.local
AD_BASE_DN=DC=yourdomain,DC=local
AD_CONTAINER_DN_BASE=OU=Users,DC=yourdomain,DC=local

# Frontend
BASE_URL=#http://127.0.0.1:8000/api/
```

#### 3. Run Migrations
```bash
python manage.py migrate
```

#### 4. Create Superuser
```bash
python manage.py createsuperuser
```

#### 5. Collect Static Files
```bash
python manage.py collectstatic
```

#### 6. Run Development Server
```bash
python manage.py runserver
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `True` or `False` |
| `DB_ENGINE` | Database engine | `mssql` |
| `DB_NAME` | Database name | `adiwa_db` |
| `DB_USER` | Database user | `sa` |
| `DB_PASSWORD` | Database password | `YourPassword` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `1433` |
| `AD_SERVER` | AD server URL | `ldap://localhost:389` |
| `AD_DOMAIN` | AD domain | `example.local` |
| `AD_BASE_DN` | AD base DN | `DC=example,DC=local` |
| `AD_CONTAINER_DN_BASE` | AD container DN | `OU=Users,DC=example,DC=local` |
| `BASE_URL` | Frontend Base-URL API |`http://127.0.0.1:8000/api/`|

### Active Directory Setup

#### Organizational Units Structure
```
DC=eissa,DC=local
└── OU=New
    ├── OU=Accountant
    ├── OU=Administrative Affairs
    ├── OU=Camera
    ├── OU=Exhibit
    ├── OU=HR
    ├── OU=IT
    ├── OU=Audit
    ├── OU=Out Work
    ├── OU=Projects
    ├── OU=Sales
    ├── OU=Supplies
    └── OU=Secretarial
```

#### Required AD Permissions
The service account needs:
- Read access to user objects
- Write access to create new user objects
- Modify DN permission for OU transfers
- Password reset permission for changing user passwords
- Read access to organizational units

## 📖 Usage

### Admin Panel

#### Create AD User
1. Login to admin panel: http://localhost:8000/admin
2. Navigate to **Users**
3. Click the **"Create AD User"** button
4. Fill in the form: username, password, first/last name, email, phone, OU
5. Click **"Create AD User"** — the user is created directly in Active Directory
6. The password is sent to AD only — **it is NOT stored in the database**
7. Run **"Sync Users"** afterward to pull the new user into the local database

#### Change AD Password
1. Navigate to **Users** → click on a user
2. Click the **"Change AD Password"** button
3. Enter the new password and confirm it
4. Click **"Change Password"** — the password is changed directly in Active Directory
5. The password is **never stored** in the Django database

#### Sync Users from AD
1. Login to admin panel: http://localhost:8000/admin
2. Navigate to **Employees**
3. Click **"Sync Users"** button
4. Users from AD will be synchronized to the database
5. **Idempotent**: syncing twice without AD changes will report `Successfully synced 0 users`

#### Transfer User OU
1. Navigate to **Employees** → **"Transfer OU"**
2. Search for user by username
3. Select new OU from dropdown
4. Choose whether to update database department
5. Click **"Transfer Employee"**
6. View transfer in audit log

### API Endpoints

#### Authentication
```bash
# Login
POST /api/auth/login/
{
  "username": "admin@example.local",
  "password": "password"
}

# Response
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token",
  "user": {
    "id": 1,
    "username": "admin@example.local",
    "is_staff": true,
    "is_superuser": true
  }
}
```

#### Employee Profile
```bash
# Get authenticated user's profile
GET /api/employee/profile/
Authorization: JWT <access-token>

# Response
{
  "id": 1,
  "username": "user@example.local",
  "full_name_en": "John Doe",
  "full_name_ar": "جون دو",
  "hire_date": "2024-01-15",
  "nid": "12345678901234",
  "job_title": {
    "id": 1,
    "title": "Software Engineer"
  },
  "department": {
    "id": 1,
    "name": "IT"
  },
  "email": "john.doe@example.local",
  "phone": "110031",
  "ou": "IT",
  "display_name": "John Doe",
  "distinguished_name": "CN=John Doe,OU=IT,OU=New,DC=example,DC=local"
}
```

### Frontend Application

#### Login Flow
1. Navigate to http://localhost:8000
2. Enter AD credentials (username@domain or username)
3. System authenticates against AD
4. JWT tokens are stored in localStorage
5. Redirected to dashboard

#### Dashboard Features
- View personal information from AD
- See employment details from database
- Display department and job title
- Show AD distinguished name

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- ReDoc: http://localhost:8000/api/schema/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

## 📁 Project Structure

```
AD_Employee/
├── ADIWA/                          # Main Django project
│   ├── __init__.py
│   ├── settings.py                 # Django settings
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI application
│   ├── asgi.py                     # ASGI application
│   └── ad_conn.py                  # AD connection handler (LDAP operations)
├── core/                           # Authentication app
│   ├── models.py                   # Custom User model
│   ├── admin.py                    # User admin (Create AD User, Change AD Password)
│   ├── views.py                    # Login view
│   ├── serializers.py              # API serializers
│   ├── auth_backends.py            # AD authentication backend
│   └── urls.py                     # Core URLs
├── employee/                       # Employee management app
│   ├── models.py                   # Employee, Department, Job, OUTransferLog models
│   ├── admin.py                    # Employee admin (Sync Users, Transfer OU)
│   ├── views.py                    # Employee API views
│   ├── serializers.py              # Employee serializers
│   └── urls.py                     # Employee URLs
├── frontend/                       # Frontend assets
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css           # Custom styles
│   │   └── js/
│   │       └── app.js              # Main JavaScript app
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── admin/
│           ├── index.html
│           ├── transfer_ou.html
│           ├── create_ad_user.html          # Create AD User form
│           ├── change_ad_password.html      # Change AD Password form
│           └── core/user/
│               ├── change_list.html         # User list (Create AD User button)
│               └── change_form.html         # User edit (Change AD Password button)
├── SERVERS_DOCKER/                 # Development AD/DB servers
│   ├── docker-compose.yml          # AD + MSSQL service definitions
│   ├── init-ad.sh                  # AD initialization (OUs + sample users)
│   ├── init-db.sh                  # Database initialization
│   ├── start.sh                    # Start all services (parallel)
│   ├── start-ad.sh                 # Start AD server only
│   ├── start-db.sh                 # Start MSSQL server only
│   ├── test.sh                     # Test services (supports: ad, db, all)
│   └── cleanup.sh                  # Cleanup (supports: ad, db, all)
├── manage.py                       # Django management
├── Dockerfile                      # Docker build file
├── docker-compose.yml              # Production compose
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
└── README.md                       # This file
```

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Make all migrations on database
python manage.py migrate 

# Creating super user to access admin panel
python manage.py createsuperuser

# Run development server with debug toolbar
DEBUG=True python manage.py runserver
```

### Development Servers (AD + MS SQL)

For local development, the `SERVERS_DOCKER` directory provides Docker-based AD and MS SQL servers with **health-check polling** (no hardcoded sleeps):

```bash
cd SERVERS_DOCKER

# Start both services (parallel, fastest)
./start.sh

# Or start individually
./start-ad.sh     # AD server only
./start-db.sh     # MSSQL server only

# Test services
./test.sh          # Test all
./test.sh ad       # Test AD only
./test.sh db       # Test MSSQL only

# Cleanup
./cleanup.sh       # Remove all
./cleanup.sh ad    # Remove AD only
./cleanup.sh db    # Remove MSSQL only
```

### AD Connection Methods

The `ADConnection` class (`ADIWA/ad_conn.py`) provides the following methods:

| Method | Description |
|--------|-------------|
| `connect_ad(username, password)` | Authenticate with AD using LDAP |
| `get_all_users_full_info(attributes)` | Retrieve all users from AD |
| `search_user_full_info(username, attributes)` | Search for a specific user |
| `search_user_dn(username)` | Get a user's Distinguished Name |
| `update_ou(username, new_ou)` | Transfer a user to a different OU |
| `create_user(username, password, ...)` | Create a new user in AD |
| `change_password(username, new_password)` | Change a user's AD password |

### Code Style

- Follow PEP 8 for Python code
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter compatible)
- Use meaningful variable and function names

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest core/tests.py

# Run with coverage
pytest --cov=.

# Run specific test class
pytest core/tests.py::UserModelTests
```
