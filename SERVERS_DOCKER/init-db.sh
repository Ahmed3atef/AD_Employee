#!/bin/bash
# MS SQL Server Database Initialization Script
# Called after MSSQL is confirmed healthy

echo "Creating adiwa_db database..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "SaPass@ADIWA" -Q "CREATE DATABASE adiwa_db" -C

if [ $? -eq 0 ]; then
    echo "Database adiwa_db created successfully!"
else
    echo "Database may already exist (this is OK)"
fi