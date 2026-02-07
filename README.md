# ADIWA - Active Directory Integration Web Application

A Django-based web application that integrates with Microsoft Active Directory (AD) for user authentication and management, with MS SQL Server as the database backend.

## ✨ Features

### Core Features
- **Active Directory Authentication**: Authenticate users against your AD infrastructure
- **Employee Management**: Manage employee profiles with AD synchronization
- **OU Transfer**: Transfer employees between Organizational Units with audit logging
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
- Session-based credential storage for AD operations

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

### Using Docker (Recommended)

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

### Active Directory Setup

#### Organizational Units Structure
```
DC=example,DC=local
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
- Modify DN permission for OU transfers
- Read access to organizational units

## 📖 Usage

### Admin Panel

#### Sync Users from AD
1. Login to admin panel: http://localhost:8000/admin
2. Navigate to "Active Directory Operations"
3. Click "Sync Users" button
4. Users from AD will be synchronized to the database

#### Transfer User OU
1. Navigate to "Employee" → "Transfer OU"
2. Search for user by username
3. Select new OU from dropdown
4. Choose whether to update database department
5. Click "Transfer Employee"
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
Authorization: Bearer <access-token>

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
ADIWA/
├── ADIWA/                      # Main Django project
│   ├── __init__.py
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI application
│   ├── asgi.py                # ASGI application
│   └── ad_conn.py             # AD connection handler
├── core/                       # Authentication app
│   ├── models.py              # User model
│   ├── views.py               # Login view
│   ├── serializers.py         # API serializers
│   ├── auth_backends.py       # AD authentication backend
│   └── urls.py                # Core URLs
├── employee/                   # Employee management app
│   ├── models.py              # Employee, Department, Job models
│   ├── views.py               # Employee API views
│   ├── admin.py               # Admin customizations
│   ├── serializers.py         # Employee serializers
│   └── urls.py                # Employee URLs
├── frontend/                   # Frontend assets
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Styles
│   │   └── js/
│   │       └── app.js         # Main JavaScript app
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── admin/
│           ├── index.html
│           └── transfer_ou.html
├── SERVERS_DOCKER/             # Development AD/DB servers
│   ├── docker-compose.yml
│   ├── init-ad.sh
│   ├── init-db.sh
│   ├── start.sh
│   ├── test.sh
│   └── cleanup.sh
├── manage.py                   # Django management
├── Dockerfile                  # Docker build file
├── docker-compose.yml          # Production compose
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
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

For local development, you can use the Docker-based AD and MS SQL servers:

```bash
cd SERVERS_DOCKER

# Start servers
./start.sh

# Test servers
./test.sh

# Cleanup (removes all data)
./cleanup.sh
```

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