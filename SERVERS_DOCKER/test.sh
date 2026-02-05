#!/bin/bash
# Test script to verify MS SQL and AD services

echo "========================================="
echo "Service Test Script"
echo "========================================="
echo ""

# Test MS SQL Server
echo "Testing MS SQL Server..."
echo "Attempting to connect and list databases..."
docker exec mssql_server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "SaPass@ADIWA" -Q "SELECT name FROM sys.databases" -C

if [ $? -eq 0 ]; then
    echo "✓ MS SQL Server is working!"
else
    echo "✗ MS SQL Server connection failed"
fi

echo ""
echo "========================================="
echo ""

# Test AD Server
echo "Testing Active Directory Server..."
AD_RUNNING=$(docker inspect -f '{{.State.Running}}' ad_server 2>/dev/null)

if [ "$AD_RUNNING" = "true" ]; then
    echo "✓ AD Server container is running"
    echo ""
    echo "Listing Samba users..."
    docker exec ad_server samba-tool user list
    echo ""
    echo "Listing OUs..."
    docker exec ad_server samba-tool ou list
else
    echo "✗ AD Server is not running"
    echo "Checking logs..."
    docker-compose logs ad_server | tail -20
fi

echo ""
echo "========================================="
echo "Test Complete"
echo "========================================="