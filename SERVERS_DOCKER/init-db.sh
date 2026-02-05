#!/bin/bash
# MS SQL Server Database Initialization Script

# Wait for SQL Server to start
echo "Waiting for SQL Server to start..."
sleep 30

# Create the database
echo "Creating adiwa_db database..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SaPass@ADIWA" -Q "CREATE DATABASE adiwa_db"

if [ $? -eq 0 ]; then
    echo "Database adiwa_db created successfully!"
else
    echo "Failed to create database!"
    exit 1
fi

echo "Database initialization completed!"