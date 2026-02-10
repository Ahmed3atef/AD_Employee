#!/bin/bash
# Test script — verify dev services
# Usage: ./test.sh         (test all)
#        ./test.sh ad      (test AD only)
#        ./test.sh db      (test MSSQL only)

TARGET="${1:-all}"

test_db() {
    echo "=== Testing MS SQL Server ==="
    MSSQL_RUNNING=$(docker inspect -f '{{.State.Running}}' mssql_server 2>/dev/null)
    if [ "$MSSQL_RUNNING" = "true" ]; then
        echo "✓ Container is running"
        docker exec mssql_server /opt/mssql-tools18/bin/sqlcmd \
            -S localhost -U sa -P "SaPass@ADIWA" \
            -Q "SELECT name FROM sys.databases" -C
        [ $? -eq 0 ] && echo "✓ MS SQL connection OK" || echo "✗ MS SQL connection failed"
    else
        echo "✗ mssql_server container is not running"
    fi
    echo ""
}

test_ad() {
    echo "=== Testing Active Directory ==="
    AD_RUNNING=$(docker inspect -f '{{.State.Running}}' ad_server 2>/dev/null)
    if [ "$AD_RUNNING" = "true" ]; then
        echo "✓ Container is running"
        echo ""
        echo "Users:"
        docker exec ad_server samba-tool user list
        echo ""
        echo "OUs:"
        docker exec ad_server samba-tool ou list
    else
        echo "✗ ad_server container is not running"
    fi
    echo ""
}

case "$TARGET" in
    db)   test_db ;;
    ad)   test_ad ;;
    all|*)
        test_db
        test_ad
        ;;
esac

echo "=== Test Complete ==="