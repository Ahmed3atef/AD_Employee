#!/bin/bash
# Cleanup script - removes all containers and volumes for fresh start

echo "========================================="
echo "Cleanup Script"
echo "========================================="
echo ""
echo "This will remove all containers and volumes."
echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

echo ""
echo "Stopping containers..."
docker-compose down

echo ""
echo "Removing volumes (this deletes all data)..."
docker-compose down -v

echo ""
echo "Removing any orphaned containers..."
docker rm -f mssql_server ad_server 2>/dev/null || true

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "You can now run ./start.sh to start fresh"