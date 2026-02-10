#!/bin/bash
# Start MS SQL Server only

set -e

echo "========================================="
echo " Starting MS SQL Server"
echo "========================================="

chmod +x init-db.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d mssql

echo ""
echo "Waiting for MS SQL to be healthy..."
MAX_WAIT=90
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' mssql_server 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo "✓ MS SQL Server is healthy (${WAITED}s)"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "  Waiting... (${WAITED}s / ${MAX_WAIT}s) - status: $STATUS"
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠ MS SQL did not become healthy in ${MAX_WAIT}s"
    echo "  Check: docker logs mssql_server"
    exit 1
fi

echo ""
echo "========================================="
echo " MS SQL Server Ready"
echo "========================================="
echo "  Host:      localhost"
echo "  Port:      1433"
echo "  Database:  adiwa_db"
echo "  User:      sa"
echo "  Password:  SaPass@ADIWA"
echo "========================================="
