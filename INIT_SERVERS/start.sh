#!/bin/bash
# Startup script for Assessment Environment

echo "========================================="
echo "Assessment Environment Setup"
echo "========================================="
echo ""

# Make initialization scripts executable
echo "Making initialization scripts executable..."
chmod +x init-db.sh init-ad.sh

# Start Docker Compose
echo ""
echo "Starting Docker containers..."
docker-compose up -d

echo ""
echo "Waiting for services to initialize..."
echo "MS SQL Server: Initializing (30 seconds)..."
sleep 30

echo "Active Directory: Initializing (90 seconds)..."
sleep 90

echo ""
echo "========================================="
echo "Services Status"
echo "========================================="
docker-compose ps

echo ""
echo "========================================="
echo "Checking Container Health"
echo "========================================="
AD_RUNNING=$(docker inspect -f '{{.State.Running}}' ad_server 2>/dev/null)
MSSQL_RUNNING=$(docker inspect -f '{{.State.Running}}' mssql_server 2>/dev/null)

if [ "$AD_RUNNING" != "true" ]; then
    echo "WARNING: AD Server is not running!"
    echo "Check logs with: docker-compose logs ad_server"
else
    echo "✓ AD Server is running"
fi

if [ "$MSSQL_RUNNING" != "true" ]; then
    echo "WARNING: MS SQL Server is not running!"
    echo "Check logs with: docker-compose logs mssql_server"
else
    echo "✓ MS SQL Server is running"
fi

echo ""
echo "========================================="
echo "Initializing Active Directory Structure"
echo "========================================="
if [ "$AD_RUNNING" = "true" ]; then
    docker exec ad_server /bin/bash /init-ad.sh
else
    echo "Skipping AD initialization - container not running"
fi

echo ""
echo "========================================="
echo "Verifying MS SQL Database"
echo "========================================="
if [ "$MSSQL_RUNNING" = "true" ]; then
    docker exec mssql_server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "SaPass@ADIWA" -Q "SELECT name FROM sys.databases WHERE name = 'adiwa_db'" -C
else
    echo "Skipping database verification - container not running"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "MS SQL Server:"
echo "  - Host: localhost"
echo "  - Port: 1433"
echo "  - Database: adiwa_db"
echo "  - User: sa"
echo "  - Password: SaPass@ADIWA"
echo ""
echo "Active Directory:"
echo "  - Domain: eissa.local"
echo "  - LDAP: ldap://localhost:389"
echo "  - Base DN: DC=eissa,DC=local"
echo "  - Admin: Administrator@eissa.local"
echo "  - Password: Admin@123456"
echo ""
echo "========================================="