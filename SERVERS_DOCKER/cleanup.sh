#!/bin/bash
# Cleanup script — remove containers and volumes
# Usage: ./cleanup.sh         (cleanup all)
#        ./cleanup.sh ad      (cleanup AD only)
#        ./cleanup.sh db      (cleanup MSSQL only)

TARGET="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup_db() {
    echo "=== Cleaning up MS SQL Server ==="
    docker rm -f mssql_server 2>/dev/null || true
    docker volume rm servers_docker_mssql_data 2>/dev/null || true
    echo "✓ MSSQL cleaned up"
    echo ""
}

cleanup_ad() {
    echo "=== Cleaning up Active Directory ==="
    docker rm -f ad_server 2>/dev/null || true
    docker volume rm servers_docker_ad_data servers_docker_ad_config 2>/dev/null || true
    echo "✓ AD cleaned up"
    echo ""
}

cleanup_all() {
    echo "This will remove ALL dev containers and volumes."
    echo "Press Ctrl+C to cancel, or Enter to continue..."
    read -r

    docker compose -f "$SCRIPT_DIR/docker-compose.yml" down -v 2>/dev/null || true
    docker rm -f mssql_server ad_server 2>/dev/null || true
    echo "✓ All cleaned up"
    echo ""
}

case "$TARGET" in
    db)  cleanup_db ;;
    ad)  cleanup_ad ;;
    all|*) cleanup_all ;;
esac

echo "Run ./start.sh (or ./start-ad.sh / ./start-db.sh) to start fresh"