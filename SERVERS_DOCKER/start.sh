#!/bin/bash
# Start all dev servers (AD + MSSQL)
# You can also run them individually:
#   ./start-ad.sh   — Active Directory only
#   ./start-db.sh   — MS SQL Server only

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================="
echo " Starting Dev Environment (AD + MSSQL)"
echo "========================================="
echo ""

# Make all scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Start both containers at once
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

# --- Wait for MSSQL health ---
echo ""
echo "[MSSQL] Waiting for health check..."
MAX_WAIT=90
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' mssql_server 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo "[MSSQL] ✓ Healthy (${WAITED}s)"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "[MSSQL]   Waiting... (${WAITED}s) - $STATUS"
done
if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[MSSQL] ⚠ Not healthy after ${MAX_WAIT}s — check: docker logs mssql_server"
fi

# --- Wait for AD health ---
echo ""
echo "[AD] Waiting for health check..."
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' ad_server 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo "[AD] ✓ Healthy (${WAITED}s)"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "[AD]   Waiting... (${WAITED}s) - $STATUS"
done
if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[AD] ⚠ Not healthy after ${MAX_WAIT}s — check: docker logs ad_server"
fi

# --- Initialize AD structure ---
AD_RUNNING=$(docker inspect -f '{{.State.Running}}' ad_server 2>/dev/null)
if [ "$AD_RUNNING" = "true" ]; then
    echo ""
    echo "[AD] Initializing OUs and users..."
    docker exec ad_server /bin/bash /init-ad.sh
fi

echo ""
echo "========================================="
echo " Dev Environment Ready"
echo "========================================="
echo ""
echo " MS SQL Server:"
echo "   Host: localhost:1433"
echo "   DB:   adiwa_db | User: sa | Pass: SaPass@ADIWA"
echo ""
echo " Active Directory:"
echo "   LDAP: ldap://localhost:389"
echo "   Domain: eissa.local | Admin: Administrator@eissa.local"
echo "   Admin Pass: Admin@123456"
echo "========================================="