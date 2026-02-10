#!/bin/bash
# Start Active Directory Server only

set -e

echo "========================================="
echo " Starting Active Directory Server"
echo "========================================="

chmod +x init-ad.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d ad_server

echo ""
echo "Waiting for AD server to be healthy..."
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' ad_server 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo "✓ AD Server is healthy (${WAITED}s)"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "  Waiting... (${WAITED}s / ${MAX_WAIT}s) - status: $STATUS"
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠ AD Server did not become healthy in ${MAX_WAIT}s"
    echo "  Container may still be starting. Check: docker logs ad_server"
    exit 1
fi

# Initialize AD structure
echo ""
echo "Initializing AD structure (OUs + users)..."
docker exec ad_server /bin/bash /init-ad.sh

echo ""
echo "========================================="
echo " AD Server Ready"
echo "========================================="
echo "  Domain:    eissa.local"
echo "  LDAP:      ldap://localhost:389"
echo "  Base DN:   DC=eissa,DC=local"
echo "  Admin:     Administrator@eissa.local"
echo "  Password:  Admin@123456"
echo "========================================="
